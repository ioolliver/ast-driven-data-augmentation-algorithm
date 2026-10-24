from decimal import Decimal, InvalidOperation
import random
import sqlglot
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name
from ..date_utils import random_date


def mutate_between(node, changelog, schema):
    if not isinstance(node, exp.Between):
        return node

    col_node = node.this
    if not isinstance(col_node, exp.Column):
        return node

    col_name = col_node.name
    table_name = get_table_name(col_node, schema)
    col_info = get_col_info(schema, table_name, col_name)

    if (not col_info or col_info["type"] not in ("number", "date")
            or "min" not in col_info or "max" not in col_info):
        return node

    old_lower = node.args.get("low").sql()
    old_upper = node.args.get("high").sql()
    col_sql = col_node.sql()

    if col_info["type"] == "number":
        min_val, max_val = col_info["min"], col_info["max"]
        values = sorted([random.randint(min_val, max_val), random.randint(min_val, max_val)])
        new_lower, new_upper = values[0], values[1]
        new_sql = f"{col_sql} BETWEEN {new_lower} AND {new_upper}"
    else:
        dates = sorted([random_date(col_info["min"], col_info["max"]), random_date(col_info["min"], col_info["max"])])
        new_lower, new_upper = dates[0].isoformat(), dates[1].isoformat()
        new_sql = f"{col_sql} BETWEEN '{new_lower}' AND '{new_upper}'"

    candidate = sqlglot.parse_one(new_sql, read=schema.get("dialect", "postgres"))
    def bound_value(bound):
        if isinstance(bound, exp.Neg) and isinstance(bound.this, exp.Literal) and bound.this.is_number:
            return -Decimal(bound.this.this)
        if isinstance(bound, exp.Literal):
            if bound.is_string:
                return bound.this
            try:
                return Decimal(bound.this)
            except InvalidOperation:
                pass
        return bound.sql()

    if all(bound_value(candidate.args[key]) == bound_value(node.args[key])
           for key in ("low", "high")):
        # Avoid a no-op without an unbounded rejection loop. An endpoint
        # singleton is still within the configured interval. If that is also
        # identical, try the other endpoint; a fixed domain may have no change.
        for endpoint in (col_info["min"], col_info["max"]):
            value = (exp.Literal.number(str(endpoint)) if col_info["type"] == "number"
                     else exp.Literal.string(str(endpoint)))
            alternative = exp.Between(this=col_node.copy(), low=value.copy(), high=value.copy())
            if any(bound_value(alternative.args[key]) != bound_value(node.args[key])
                   for key in ("low", "high")):
                candidate = alternative
                new_sql = candidate.sql(dialect=schema.get("dialect", "postgres"))
                break
        else:
            return node

    changelog.append({
        "old_line": f"{col_sql} BETWEEN {old_lower} AND {old_upper}",
        "new_line": new_sql,
    })

    return candidate
