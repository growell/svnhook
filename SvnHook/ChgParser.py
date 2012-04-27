"""Change Line Parser Singleton

Use the first "svnlook change" line to determine how to separate the
change flags from the change path. Subsequent change lines are parsed
using the previously-determined format.
"""
__version__ = "1.0"
__all__     = ['ChgParser']

class ChgParser(object):
    """Change record parser singleton"""
    _instance = None
    _delimidx = None

    def __new__(this, *args, **kwargs):
        if not this._instance:
            this._instance = super(
                ChgParser, this).__new__(this, *args, **kwargs)
        return this._instance

    def parse(self, chgline):
        """Split a change line into type and path."""

        # If the delimiter index isn't known, figure it out. Scan the
        # characters of the first change line.
        if not self._delimidx:
            self._delimidx = state = 0
            for chgchar in chgline:

                # Look for the first non-space character.
                if state == 0 and chgchar != ' ': state = 1

                # Look for the next space character.
                elif state == 1 and chgchar == ' ': state = 2

                # Look for the first path character.
                elif state == 2 and chgchar != ' ': break
                
                # Increment the delimiter position.
                self._delimidx += 1

        # Split the change line, using the delimiter index.
        return [
            chgline[:self._delimidx - 1], chgline[self._delimidx:]]

########################### end of file ##############################
