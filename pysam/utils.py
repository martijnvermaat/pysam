from pysam.cutils import _pysam_dispatch


class SamtoolsError(Exception):
    '''exception raised in case of an error incurred in the samtools
    library.'''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class PysamDispatcher(object):
    '''The dispatcher emulates the samtools/bctools command line.

    Captures stdout and stderr.

    Raises a :class:`pysam.SamtoolsError` exception in case samtools
    exits with an error code other than 0.

    Some command line options are associated with parsers.  For
    example, the samtools command "pileup -c" creates a tab-separated
    table on standard output. In order to associate parsers with
    options, an optional list of parsers can be supplied. The list
    will be processed in order checking for the presence of each
    option.

    If no parser is given or no appropriate parser is found, the
    stdout output of samtools/bcftools commands will be returned.

    '''

    dispatch = None
    parsers = None
    collection = None

    def __init__(self, collection, dispatch, parsers):
        self.collection = collection
        self.dispatch = dispatch
        self.parsers = parsers
        self.stderr = []
        
    def __call__(self, *args, **kwargs):
        '''execute a samtools command.

        Keyword arguments:
        catch_stdout -- redirect stdout from the samtools command and
            return as variable (default True)
        raw -- ignore any parsers associated with this samtools command.
        split_lines -- return stdout and stderr as a list of strings.
        '''
        retval, stderr, stdout = _pysam_dispatch(
            self.collection,
            self.dispatch,
            args,
            catch_stdout=kwargs.get("catch_stdout", True))

        if kwargs.get("split_lines", False):
            stdout = stdout.splitlines()
            if stderr:
                stderr = stderr.splitlines()

        if retval:
            raise SamtoolsError(
                "%s returned with error %i: "
                "stdout=%s, stderr=%s" %
                (self.collection,
                 retval, 
                 "\n".join(stdout),
                 "\n".join(stderr)))

        self.stderr = stderr

        # call parser for stdout:
        if not kwargs.get("raw") and stdout and self.parsers:
            for options, parser in self.parsers:
                for option in options:
                    if option not in args:
                        break
                else:
                    return parser(stdout)

        return stdout

    def get_messages(self):
        return self.stderr

    def usage(self):
        '''return the samtools usage information for this command'''
        retval, stderr, stdout = csamtools._samtools_dispatch(
            self.dispatch)
        return stderr

