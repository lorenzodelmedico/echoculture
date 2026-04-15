{% macro normalize_genre(col) %}
    INITCAP(SPLIT_PART({{ col }}, ' ', 1))
    || LOWER(SUBSTRING({{ col }} FROM LENGTH(SPLIT_PART({{ col }}, ' ', 1)) + 1))
{% endmacro %}
