from dataset.object_mapping import OBJECT_MAPPING


def translate_object(class_name):
    return OBJECT_MAPPING.get(class_name, class_name)