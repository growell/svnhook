"""Change Listing Item Class

Use the first "svnlook change" line to determine how to separate the
change flags from the change path. Subsequent change lines are parsed
using the previously-determined format.
"""
__version__ = '3.00'
__all__     = ['ChangeItem']

class ChangeItem(object):
    """Change Listing Item Class"""

    def __init__(self, chgline):
        """Parse a change line.

        Arguments:

        - chgline -- Svnlook line to parse.

        """
        # If the delimiter index isn't known, figure it out. Scan the
        # characters of the first change line.
        if not self.delimidx:
            self.delimidx = state = 0
            for chgchar in chgline:

                # Look for the first non-space character.
                if state == 0 and chgchar != ' ': state = 1

                # Look for the next space character.
                elif state == 1 and chgchar == ' ': state = 2

                # Look for the first path character.
                elif state == 2 and chgchar != ' ': break
                
                # Increment the delimiter position.
                self.delimidx += 1

        # Parse the change line.
        self.type = chgline[:self.delimidx - 1]
        self.path = chgline[self.delimidx:]

        # Initialize the replaced path flag.
        self.replaced = False

    def is_add(self):
        """Is the change an add operation?"""
        return re.match(r'A', self.type) != None

    def is_delete(self):
        """Is the change a delete operation?"""
        return re.match(r'D', self.type) != None

    def is_update(self):
        """Is the change a content or property update?"""
        return re.search(r'U', self.type) != None

    def is_update_content(self):
        """Is the change a content update?"""
        return re.match(r'U', self.type) != None

    def is_update_property(self):
        """Is the change a property update?"""
        return re.match(r'_U', self.type) != None

    def is_update_all(self):
        """Is the change both a content and property update?"""
        return re.match(r'UU', self.type) != None

########################### end of file ##############################
