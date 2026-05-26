import random

from sqlglot import exp

from schema_utils import get_col_info, get_table_name


DEFAULT_DISTANCE_MIN_M = 100
DEFAULT_DISTANCE_MAX_M = 5000
DEFAULT_BUFFER_MIN_M = 100
DEFAULT_BUFFER_MAX_M = 3000
SET_OPERATION_TARGETS = ("ST_Union", "ST_Difference")
INEQ_CLASSES = (exp.GT, exp.LT, exp.GTE, exp.LTE)


def mutate_distance_threshold(node, changelog, schema, state):
    if not isinstance(node, INEQ_CLASSES):
        return node

    if isinstance(node.left, exp.StDistance) and _is_numeric_literal(node.right):
        distance_node = node.left
        threshold_node = node.right
        threshold_is_right = True
    elif isinstance(node.right, exp.StDistance) and _is_numeric_literal(node.left):
        distance_node = node.right
        threshold_node = node.left
        threshold_is_right = False
    else:
        return node

    old_key = _literal_key(threshold_node)
    old_value = _numeric_value(threshold_node)
    min_value, max_value = _range_for_node(
        distance_node,
        schema,
        "distance_min_m",
        "distance_max_m",
        DEFAULT_DISTANCE_MIN_M,
        DEFAULT_DISTANCE_MAX_M,
    )
    new_value = _coordinated_numeric_change(
        state,
        "postgis_distance_by_old",
        old_key,
        old_value,
        min_value,
        max_value,
    )

    if new_value == old_value:
        return node

    old_sql = node.sql(dialect="postgres")
    new_threshold = exp.Literal.number(str(new_value))
    if threshold_is_right:
        node.set("expression", new_threshold)
    else:
        node.set("this", new_threshold)

    changelog.append({
        "old_line": old_sql,
        "new_line": node.sql(dialect="postgres"),
        "tip": f"Limite de ST_Distance alterado de {old_key} para {new_value}",
    })
    return node

def mutate_postgis(node, changelog, schema, state):
    if not isinstance(node, exp.Anonymous):
        return node

    function_name = _function_name(node)

    if function_name == "ST_DWITHIN":
        return _mutate_dwithin_distance(node, changelog, schema, state)
    if function_name == "ST_BUFFER":
        return _mutate_buffer_radius(node, changelog, schema, state)
    if function_name == "ST_INTERSECTS":
        return _mutate_intersects_buffer_pair(node, changelog, schema, state)
    if function_name == "ST_INTERSECTION":
        return _mutate_intersection_operation(node, changelog)

    return node


def _function_name(node):
    return str(node.args.get("this", "")).upper()


def _expressions(node):
    return list(node.args.get("expressions") or [])


def _mutate_buffer_radius(node, changelog, schema, state):
    expressions = _expressions(node)
    if len(expressions) < 2 or not _is_numeric_literal(expressions[1]):
        return node

    radius_node = expressions[1]
    old_key = _literal_key(radius_node)
    old_value = _numeric_value(radius_node)
    min_value, max_value = _range_for_node(
        node,
        schema,
        "buffer_min_m",
        "buffer_max_m",
        DEFAULT_BUFFER_MIN_M,
        DEFAULT_BUFFER_MAX_M,
    )
    new_value = _coordinated_numeric_change(
        state,
        "postgis_buffer_radius_by_old",
        old_key,
        old_value,
        min_value,
        max_value,
    )

    if new_value == old_value:
        return node

    old_sql = node.sql(dialect="postgres")
    expressions[1] = exp.Literal.number(str(new_value))
    node.set("expressions", expressions)

    changelog.append({
        "old_line": old_sql,
        "new_line": node.sql(dialect="postgres"),
        "tip": f"Raio de ST_Buffer alterado de {old_key} m para {new_value} m",
    })

    return node


def _mutate_dwithin_distance(node, changelog, schema, state):
    expressions = _expressions(node)
    if len(expressions) < 3 or not _is_numeric_literal(expressions[2]):
        return node

    distance_node = expressions[2]
    old_key = _literal_key(distance_node)
    old_value = _numeric_value(distance_node)
    min_value, max_value = _range_for_node(
        node,
        schema,
        "distance_min_m",
        "distance_max_m",
        DEFAULT_DISTANCE_MIN_M,
        DEFAULT_DISTANCE_MAX_M,
    )
    new_value = _coordinated_numeric_change(
        state,
        "postgis_distance_by_old",
        old_key,
        old_value,
        min_value,
        max_value,
    )

    if new_value == old_value:
        return node

    old_sql = node.sql(dialect="postgres")
    expressions[2] = exp.Literal.number(str(new_value))
    node.set("expressions", expressions)

    changelog.append({
        "old_line": old_sql,
        "new_line": node.sql(dialect="postgres"),
        "tip": f"Distância de ST_DWithin alterada de {old_key} m para {new_value} m",
    })

    return node


def _mutate_intersection_operation(node, changelog):
    target_function = random.choice(SET_OPERATION_TARGETS)
    old_sql = node.sql(dialect="postgres")
    node.set("this", target_function)

    changelog.append({
        "old_line": old_sql,
        "new_line": node.sql(dialect="postgres"),
        "tip": f"Operação espacial alterada de ST_Intersection para {target_function}",
    })

    return node


def _mutate_intersects_buffer_pair(node, changelog, schema, state):
    expressions = _expressions(node)
    if len(expressions) != 2:
        return node

    left = _extract_buffer_call(expressions[0])
    right = _extract_buffer_call(expressions[1])
    if not left or not right or left["radius_key"] != right["radius_key"]:
        return node

    current_distance = left["radius_value"] * 2
    min_value, max_value = _range_for_node(
        node,
        schema,
        "distance_min_m",
        "distance_max_m",
        DEFAULT_DISTANCE_MIN_M,
        DEFAULT_DISTANCE_MAX_M,
    )
    old_key = f"buffer_intersects:{left['radius_key']}"
    new_distance = _coordinated_numeric_change(
        state,
        "postgis_distance_by_old",
        old_key,
        current_distance,
        min_value,
        max_value,
    )

    old_sql = node.sql(dialect="postgres")
    new_node = exp.Anonymous(
        this="ST_DWithin",
        expressions=[
            left["geometry_arg"].copy(),
            right["geometry_arg"].copy(),
            exp.Literal.number(str(new_distance)),
        ],
    )

    changelog.append({
        "old_line": old_sql,
        "new_line": new_node.sql(dialect="postgres"),
        "tip": (
            "ST_Intersects com buffers reescrito para ST_DWithin "
            f"com distância de {new_distance} m"
        ),
    })

    return new_node


def _extract_buffer_call(node):
    candidate = node
    if isinstance(candidate, exp.Cast):
        candidate = candidate.this

    if not isinstance(candidate, exp.Anonymous) or _function_name(candidate) != "ST_BUFFER":
        return None

    expressions = _expressions(candidate)
    if len(expressions) < 2 or not _is_numeric_literal(expressions[1]):
        return None

    return {
        "geometry_arg": expressions[0],
        "radius_key": _literal_key(expressions[1]),
        "radius_value": _numeric_value(expressions[1]),
    }


def _coordinated_numeric_change(state, state_key, old_key, old_value, min_value, max_value):
    values_by_old = state.setdefault(state_key, {})
    if old_key not in values_by_old:
        values_by_old[old_key] = _random_int_excluding(min_value, max_value, old_value)
    return values_by_old[old_key]


def _random_int_excluding(min_value, max_value, excluded_value):
    if min_value > max_value:
        min_value, max_value = max_value, min_value

    if min_value == max_value:
        return min_value

    for _ in range(10):
        value = random.randint(min_value, max_value)
        if value != excluded_value:
            return value

    return min_value if excluded_value != min_value else max_value


def _range_for_node(node, schema, min_key, max_key, default_min, default_max):
    for column in node.find_all(exp.Column):
        table_name = get_table_name(column)
        col_info = get_col_info(schema, table_name, column.name) or get_col_info(schema, None, column.name)
        if col_info and col_info.get(min_key) is not None and col_info.get(max_key) is not None:
            return int(col_info[min_key]), int(col_info[max_key])

    return default_min, default_max


def _is_numeric_literal(node):
    if not isinstance(node, exp.Literal) or node.is_string:
        return False

    try:
        int(float(node.this))
    except (TypeError, ValueError):
        return False

    return True


def _numeric_value(node):
    return int(float(node.this))


def _literal_key(node):
    value = _numeric_value(node)
    return str(value)
