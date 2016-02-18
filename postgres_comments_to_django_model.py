#!/usr/bin/env python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "migration_admin.settings")

from django.db import connections
cur = connections['stage_i'].cursor()

sql = """
SELECT c.table_schema,c.table_name,c.column_name,pgd.description
FROM pg_catalog.pg_statio_all_tables as st
  inner join pg_catalog.pg_description pgd on (pgd.objoid=st.relid)
  inner join information_schema.columns c on (pgd.objsubid=c.ordinal_position
    and  c.table_schema=st.schemaname and c.table_name=st.relname);
"""

cur.execute(sql)
comments_table = [{'table': x[1], 'field': x[2], 'comment': x[3]} for x in cur.fetchall()]
print(comments_table)

import ast

with open('C:/Users/user/Documents/Work/migration_admin/apps/norm_admin/models.py', encoding='utf-8') as f:
    c = f.read()

p = ast.parse(c)

for o in p.body:
    if not isinstance(o, ast.ClassDef):
        continue
    # Классы
    definitions = []
    db_table = ''
    cls = None
    for d in o.body:
        if isinstance(d, ast.ClassDef) and d.name == 'Meta':
            cls = d
            for a in d.body:
                if isinstance(a, ast.Assign):
                    if a.targets[0].id == 'db_table':
                        db_table = a.value.s

    if not db_table:
        continue

    for d in o.body:
        if isinstance(d, ast.Assign):
            try:
                row = next(x for x in comments_table if x['table'] == db_table and (x['field'] == d.targets[0].id or x['field'] == d.targets[0].id + '_id'))
                kw = ast.parse("a(verbose_name='%s')" % row['comment']).body[0].value.keywords[0]
                d.value.keywords.insert(0, kw)
                print('Modified: %s, %s' % (d.targets[0].id, row['comment']))
            except StopIteration:
                print('Not found: %s %s' % (db_table, d.targets[0].id))

import codegen

print(codegen.to_source(p))
