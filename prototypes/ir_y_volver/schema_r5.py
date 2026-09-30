"""Dependency-free validator for the explicit JSON Schema subset emitted by R5.

Public schemas are standard draft 2020-12; release QA also uses jsonschema.
This evaluator is intentionally scoped, not a general JSON Schema implementation.
"""
import re
from .snapshot_validation import finite_tree, require


def validate(value,schema,root=None):
    finite_tree(value);root=schema if root is None else root
    if '$ref' in schema:
        return validate(value,root['$defs'][schema['$ref'].split('/')[-1]],root)
    for keyword in ('anyOf','oneOf'):
        if keyword in schema:
            matches=0
            for option in schema[keyword]:
                try: validate(value,option,root);matches+=1
                except ValueError: pass
            require(matches>=1 if keyword=='anyOf' else matches==1,'schema alternatives')
    if 'allOf' in schema:
        for option in schema['allOf']: validate(value,option,root)
    if 'if' in schema:
        try: validate(value,schema['if'],root)
        except ValueError: pass
        else: validate(value,schema.get('then',{}),root)
    if 'const' in schema:
        require(type(value) is type(schema['const']) and value==schema['const'],'schema const')
    if 'enum' in schema:
        require(any(type(value) is type(v) and value==v for v in schema['enum']),'schema enum')
    if 'type' in schema:
        types=schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        matches={'object':type(value) is dict,'array':type(value) is list,'string':type(value) is str,
                 'integer':type(value) is int,'number':type(value) in (int,float),'boolean':type(value) is bool,'null':value is None}
        require(any(matches[t] for t in types),'schema type')
    if type(value) is dict:
        props=schema.get('properties',{})
        require(set(schema.get('required',[]))<=value.keys(),'schema required')
        if schema.get('additionalProperties') is False: require(value.keys()<=props.keys(),'schema extra property')
        for k,v in value.items():
            if k in props: validate(v,props[k],root)
    if type(value) is list:
        require(len(value)>=schema.get('minItems',0) and len(value)<=schema.get('maxItems',10**20),'schema array length')
        for i,v in enumerate(value):
            prefix=schema.get('prefixItems',[])
            validate(v,prefix[i] if i<len(prefix) else schema.get('items',{}),root)
    if type(value) is str:
        require(len(value)>=schema.get('minLength',0),'schema string length')
        if 'pattern' in schema: require(re.search(schema['pattern'],value) is not None,'schema pattern')
    if type(value) in (int,float):
        require(schema.get('minimum',-float('inf'))<=value<=schema.get('maximum',float('inf')),'schema range')
