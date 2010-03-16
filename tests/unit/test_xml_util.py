import unittest
from datetime import datetime
from braintree.util.utc import UTC
from braintree.util.xml_util import XmlUtil

class TestXmlUtil(unittest.TestCase):
    def test_dict_from_xml_simple(self):
        xml = """
        <container>val</container>
        """
        expected = {"container": "val"}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_typecasts_ints(self):
        xml = """
        <container type="integer">1</container>
        """
        expected = {"container": 1}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_typecasts_nils(self):
        xml = """
        <root>
          <a_nil_value nil="true"></a_nil_value>
          <an_empty_string></an_empty_string>
        </root>
        """
        expected = {"root": {"a_nil_value": None, "an_empty_string": ""}}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_typecasts_booleans(self):
        xml = """
        <root>
          <casted-true type="boolean">true</casted-true>
          <casted-one type="boolean">1</casted-one>
          <casted-false type="boolean">false</casted-false>
          <casted-anything type="boolean">anything</casted-anything>
          <uncasted-true>true</uncasted-true>
        </root>
        """
        expected = {
            "root": {
                "casted_true": True,
                "casted_one": True,
                "casted_false": False,
                "casted_anything": False,
                "uncasted_true": "true"
            }
        }
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_typecasts_dates_and_times(self):
        xml = """
        <root>
          <created-at type="datetime">2009-10-28T10:19:49Z</created-at>
        </root>
        """
        expected = {"root": {"created_at": datetime(2009, 10, 28, 10, 19, 49)}}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))


    def test_dict_from_xml_with_dashes(self):
        xml = """
        <my-item>val</my-item>
        """
        expected = {"my_item": "val"}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_nested(self):
        xml = """
        <container>
            <elem>val</elem>
        </container>
        """
        expected = {"container": {"elem": "val"}}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_array(self):
        xml = """
        <container>
            <elements type="array">
                <elem>val1</elem>
                <elem>val2</elem>
                <elem>val3</elem>
            </elements>
        </container>
        """
        expected = {"container": {"elements": ["val1", "val2", "val3"]}}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_dict_from_xml_array_of_hashes(self):
        xml = """
        <container>
            <elements type="array">
                <elem><val>val1</val></elem>
                <elem><val>val2</val></elem>
                <elem><val>val3</val></elem>
            </elements>
        </container>
        """
        expected = {"container": {"elements": [{"val": "val1"}, {"val": "val2"}, {"val": "val3"}]}}
        self.assertEqual(expected, XmlUtil.dict_from_xml(xml))

    def test_xml_from_dict_simple(self):
        dict = {"a": "b"}
        self.assertEqual(dict, self.__xml_and_back(dict))

    def test_xml_from_dict_nested(self):
        dict = {"container": {"item": "val"}}
        self.assertEqual(dict, self.__xml_and_back(dict))

    def test_xml_from_dict_with_array(self):
        dict = {"container": {"elements": ["val1", "val2", "val3"]}}
        self.assertEqual(dict, self.__xml_and_back(dict))

    def test_xml_from_dict_with_array_of_hashes(self):
        dict = {"container": {"elements": [{"val": "val1"}, {"val": "val2"}, {"val": "val3"}]}}
        self.assertEqual(dict, self.__xml_and_back(dict))

    def test_xml_from_dict_retains_underscores(self):
        dict = {"container": {"my_element": "val"}}
        self.assertEqual(dict, self.__xml_and_back(dict))

    def __xml_and_back(self, dict):
        return XmlUtil.dict_from_xml(XmlUtil.xml_from_dict(dict))
