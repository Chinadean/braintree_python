class Generator:
    def __init__(self, dict):
        self.dict = dict

    def generate(self):
        return self.__generate_dict(self.dict)

    def __generate_dict(self, dictionary):
        xml = ""
        for key in dictionary.keys():
            xml += self.__generate_node(key, dictionary[key])
        return xml

    def __generate_list(self, list):
        xml = ""
        for item in list:
            xml += self.__generate_node("item", item)
        return xml

    def __generate_node(self, key, value):
        open_tag = "<" + key + ">"
        close_tag = "</" + key + ">"

        if type(value) == str:
            return open_tag + value + close_tag
        elif type(value) == dict:
            return open_tag + self.__generate_dict(value) + close_tag
        elif type(value) == list:
            open_tag = "<" + key + " type=\"array\">"
            return open_tag + self.__generate_list(value) + close_tag

