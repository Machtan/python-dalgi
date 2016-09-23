import ftoml as toml

from .resources import Resources
from .entity_group import EntityGroup

def load_level(level: str, group: EntityGroup, resources: Resources, constructors):
    """Loads the level in the given file into the given group"""
    with open(level) as f:
        data = toml.loads(f.read())
    
    for resource_file in data.get("resources", []):
        print("Loading resource {!r}".format(resource_file))
        resources.load(resource_file+".toml")
    
    for ent in data.get("entities", []):
        t = ent["type"]
        if t not in constructors:
            raise ValueError("Class {!r} not found!".format(t)) from e
        constructor = constructors[t]
        if type(constructor) is not type:
            raise TypeError("{!r} ({}) is not a valid constructor!".format(
                t, type(constructor)
            ))
        x, y = ent["pos"]
        entity = constructor(x, y, resources)
        if "layer" in ent:
            group.add(entity, draw_layer=ent["layer"])
        else:
            group.add(entity)
        
        if "tags" in ent:
            group.add_tags(entity, *ent["tags"])
            