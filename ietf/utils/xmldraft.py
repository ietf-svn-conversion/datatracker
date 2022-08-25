# Copyright The IETF Trust 2022, All Rights Reserved
# -*- coding: utf-8 -*-
import io
import re
import xml2rfc

import debug  # pyflakes: ignore

from contextlib import ExitStack

from .draft import Draft


class XMLDraft(Draft):
    """Draft from XML source

    Not all methods from the superclass are implemented yet.
    """
    def __init__(self, xml_file):
        """Initialize XMLDraft instance

        :parameter xml_file: path to file containing XML source
        """
        super().__init__()
        # cast xml_file to str so, e.g., this will work with a Path
        self.xmltree, self.xml_version = self.parse_xml(str(xml_file))
        self.xmlroot = self.xmltree.getroot()
        self.filename, self.revision = self._parse_docname()

    @staticmethod
    def parse_xml(filename):
        """Parse XML draft

        Converts to xml2rfc v3 schema, then returns the root of the v3 tree and the original
        xml version.
        """
        orig_write_out = xml2rfc.log.write_out
        orig_write_err = xml2rfc.log.write_err
        parser_out = io.StringIO()
        parser_err = io.StringIO()

        with ExitStack() as stack:
            @stack.callback
            def cleanup():  # called when context exited, even if there's an exception
                xml2rfc.log.write_out = orig_write_out
                xml2rfc.log.write_err = orig_write_err

            xml2rfc.log.write_out = parser_out
            xml2rfc.log.write_err = parser_err

            parser = xml2rfc.XmlRfcParser(filename, quiet=True)
            try:
                tree = parser.parse()
            except Exception as e:
                raise XMLParseError(parser_out.getvalue(), parser_err.getvalue()) from e

            xml_version = tree.getroot().get('version', '2')
            if xml_version == '2':
                v2v3 = xml2rfc.V2v3XmlWriter(tree)
                tree.tree = v2v3.convert2to3()
        return tree, xml_version

    def _document_name(self, anchor):
        """Guess document name from reference anchor

        Looks for series numbers and removes leading 0s from the number.
        """
        anchor = anchor.lower()  # always give back lowercase
        label = anchor.rstrip('0123456789')  # remove trailing digits
        if label in ['rfc', 'bcp', 'fyi', 'std']:
            number = int(anchor[len(label):])
            return f'{label}{number}'
        return anchor

    def _reference_section_type(self, section_name):
        """Determine reference type from name of references section"""
        if section_name:
            section_name = section_name.lower()
            if 'normative' in section_name:
                return self.REF_TYPE_NORMATIVE
            elif 'informative' in section_name:
                return self.REF_TYPE_INFORMATIVE
        return self.REF_TYPE_UNKNOWN

    def _reference_section_name(self, section_elt):
        section_name = section_elt.findtext('name')
        if section_name is None and 'title' in section_elt.keys():
            section_name = section_elt.get('title')  # fall back to title if we have it
        return section_name

    def _parse_docname(self):
        docname = self.xmlroot.attrib.get('docName')
        revmatch = re.match(
            r'^(?P<filename>.+?)(?:-(?P<rev>[0-9][0-9]))?$',
            docname,

        )
        if revmatch is None:
            raise ValueError('Unable to parse docName')
        # If a group had no match it is None
        return revmatch.group('filename'), revmatch.group('rev')

    def get_title(self):
        return self.xmlroot.findtext('front/title').strip()

    # todo fix the implementation of XMLDraft.get_abstract()
    #
    # This code was pulled from ietf.submit.forms where it existed for some time.
    # It does not work, at least with modern xml2rfc. This assumes that the abstract
    # is simply text in the front/abstract node, but the XML schema wraps the actual
    # abstract text in <t> elements (and allows <dl>, <ol>, and <ul> as well). As a
    # result, this method normally returns an empty string, which is later replaced by
    # the abstract parsed from the rendered text. For now, I a commenting this out
    # and making it explicit that the abstract always comes from the text format.
    #
    # def get_abstract(self):
    #     """Extract the abstract"""
    #     abstract = self.xmlroot.findtext('front/abstract')
    #     return abstract.strip() if abstract else ''

    def get_author_list(self):
        """Get detailed author list

        Returns a list of dicts with the following keys:
            name, first_name, middle_initial, last_name,
            name_suffix, email, country, affiliation
        Values will be None if not available
        """
        result = []
        empty_author = {
            k: None for k in [
                'name', 'first_name', 'middle_initial', 'last_name',
                'name_suffix', 'email', 'country', 'affiliation',
            ]
        }

        for author in self.xmlroot.findall('front/author'):
            info = {
                'name': author.attrib.get('fullname'),
                'email': author.findtext('address/email'),
                'affiliation': author.findtext('organization'),
            }
            elem = author.find('address/postal/country')
            if elem is not None:
                ascii_country = elem.get('ascii', None)
                info['country'] = ascii_country if ascii_country else elem.text
            for item in info:
                if info[item]:
                    info[item] = info[item].strip()
            result.append(empty_author | info)  # merge, preferring info
        return result

    def get_refs(self):
        """Extract references from the draft"""
        refs = {}
        # accept nested <references> sections
        for section in self.xmlroot.findall('back//references'):
            ref_type = self._reference_section_type(self._reference_section_name(section))
            for ref in (section.findall('./reference') + section.findall('./referencegroup')):
                refs[self._document_name(ref.get('anchor'))] = ref_type
        return refs


class XMLParseError(Exception):
    """An error occurred while parsing"""
    def __init__(self, out: str, err: str, *args):
        super().__init__(*args)
        self._out = out
        self._err = err

    def parser_msgs(self):
        return self._out.splitlines() + self._err.splitlines()
