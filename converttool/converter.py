from converttool import *
from converttool.formats import Format
from converttool.exceptions import *
from click import progressbar
import re
import codecs
import unicodecsv as csv

log = logging.getLogger('converttool.Converter')

class Converter:
    """Class to handle the conversion of data
    
    Converter class takes the csv_file and the output format
    as input and converts the csv data into the required output
    format. The output name is optional, and if not supplied, 
    Converter will create the output with the name 
    `output`.<format_name>

    """
    def __init__(self, csv_file, output_format, output_name=None, pretty=False, loglevel="notset", strict=False):
        """Method to initialize converter

        :param str csv_file: Name of the csv file
        :param str output_format: Format of the output
        :param str output_name: Name of the output to be created. Defaults        to output.<format_name>, if a name is given, the tool will 
        create files in the format <name>.<format_name>
        :param bool pretty: A flag to specify pretty printing
        :param str loglevel: A loglevel for the logging module
        :param bool strict: Boolean for validation. If set, will raise 
        ValidationError. False by default, and only removes 

        """
        self.csv_file = csv_file
        self.output_format = output_format
        self.output_name = output_name
        self.pretty=pretty
        #TODO: Validate before parsing
        self.data = self.parse_csv()
        log.setLevel(getattr(logging, loglevel.upper()))
        self.loglevel = loglevel
        self.strict = strict
        self.validate_data()

    def parse_csv(self):
        """Method to parse the csv and load the data"""
        #TODO: convert into list comprehension
        log.info("Parsing CSV")
        data = []
        try:
            log.debug("Trying to open {}".format(self.csv_file))
            with open(self.csv_file) as f:
                length = len(f.readlines())
                f.seek(0)
                f_csv = csv.DictReader(f, encoding="utf-8")
                with progressbar(f_csv,
                        label="Reading from CSV\t",
                        length=length) as bar:
                    for row in bar:
                        data.append(row)
            return data
        except IOError:
            log.debug("IO Error Occured")
            raise CSVNotFound("{} not found!".format(self.csv_file))

    def validate_data(self):
        """Method to validate the data read from the csv file"""
        log.info("Validating Data")
        for d in self.data:
            validate = all([Converter._is_rating_valid(d['stars']),
                    Converter._is_name_unicode(d['name']), 
                    Converter._is_uri_valid(d['uri'])])
            if not validate:
                if self.strict:
                    raise ValidationError("Validation Failed. Please check your csv file for invalid names/stars/url")
                else:
                    #Remove d from self.data
                    pass

    @classmethod
    def _is_rating_valid(cls, rating):
        """Method to check if the rating of a hotel is valid or invalid
        :param str rating: rating of the hotel 
        """
        if not isinstance(rating, unicode):
            raise ValueError("rating should be strictly unicode")
        return (1 <= int(rating) <= 5)

    @classmethod
    def _is_uri_valid(cls, uri):
        """Method to check if the uri is a valid uri or an invalid uri
        Rules to define an invalid url(keeing it simple):
            * The uri cannot contain any space 
            * If the uri contains `://` then it can start with only 
              http or https
            * uri should not end with a port number
            * Should contain atleast 1 period (For domain)
        """
        # URI's should be string
        if not isinstance(uri, unicode):
            log.debug("Non-unicoded URI passed")
            raise ValueError("URI has to be a unicoded string")
        # Ignore any url with a space in it
        if ' ' in uri:
            log.debug("Validation failed for {}: space".format(uri))
            return False
        # It should be http or https scheme
        if '://' in uri:
            if not re.findall(r"^https?://", uri):
                log.debug("Validation failed for {}: http/https required".format(uri))
                return False
        # Sorry port numbers are not allowed
        if re.findall(r":[0-9]*$", uri):
            log.debug("Validation failed for {}: port number found".format(uri))
            return False
        # atlease one period required.
        if '.' not in uri:
            log.debug("Validation failed for {}: period not found".format(uri))
            return False
        return True

    @classmethod
    def _is_name_unicode(cls, name):
        """Method to check if the address is in unicode or plain ascii
        """
        return isinstance(name, unicode)

    def convert(self):
        """Method to convert the csv data into the specified formats"""
        log.info("Converting to other formats")
        with progressbar(self.output_format,
                label="Converting {}\t".format('|'.join(self.output_format)),
                length=len(self.output_format)) as bar:
            for format in bar:
                log.debug("Process for :{} format".format(format))
            self.formatter = Format(output_format=format, csv_data=self.data, output_name=self.output_name, pretty=self.pretty, loglevel=self.loglevel)
            self.formatter.convert_data()
