"""Regular Expression Tag Class

Evaluate text against regular expression details provided by a hook
configuration XML tag.
"""
__version__ = '1.0'
__all__     = ['RegexTag']

import re

class RegexTag(object):

    def __init__(self, regextag, *args):
        """Construct instance from regular expression tag.

        Arguments:

        - regextag -- Element instance for the regex tag.
        - *args -- Regular expression flags.

        """
        if regextag.text == None:
            raise RuntimeError(
                'Required tag content missing: {}'.format(regextag.tag))

        # Compile the regular expression.
        self.regex = re.compile(regextag.text, *args)

        # Determine the true/false sense to apply to the result.
        self.sense = (re.match(r'(1|true|yes)$',
                              regextag.get('sense', default='1'),
                              re.IGNORECASE) != None)

    def match(self, text):
        """Compare start of the text to the regular expression.

        Arguments:

        - text -- Text to be evaluated.

        """
        if self.sense:
            return (self.regex.match(text) != None)
        else:
            return (self.regex.match(text) == None)

    def search(self, text):
        """Compare all of the text to the regular expression.

        Arguments:

        - text -- Text to be evaluated.

        """
        if self.sense:
            return (self.regex.search(text) != None)
        else:
            return (self.regex.search(text) == None)

########################### end of file ##############################
