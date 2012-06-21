#!/usr/bin/env python
######################################################################
# SvnHook Test SMTP Server Thread Class
######################################################################
__all__ = ['SmtpSink']

# From SmtpMailsink - Copyright 2005 Aviarc Corporation
# Written by Adam Feuer, Matt Branthwaite, and Troy Frever

import asyncore, threading, socket, smtpd, StringIO

class SmtpSinkServer(smtpd.SMTPServer):
    """Unix Mailbox File SMTP Server Class"""
    __version__ = 'SMTP Test Sink version 1.00'

    def __init__(self, *args, **kwargs):
        smtpd.SMTPServer.__init__(self, *args, **kwargs)
        self.mailboxFile = None

    def setMailboxFile(self, mailboxFile):
        """Set the Unix mailbox file."""
        self.mailboxFile = mailboxFile
        
    def process_message(self, peer, mailfrom, rcpttos, data):
        """Add a message to the mailbox file."""
        if self.mailboxFile is not None:
            self.mailboxFile.write('From {}\n'.format(mailfrom))
            self.mailboxFile.write(data)
            self.mailboxFile.write('\n\n')
            self.mailboxFile.flush()

class SmtpSink(threading.Thread):
    """Unix Mailbox SMTP Server Thread Class"""
    SHUTDOWN_DELAY = 0.001

    def __init__(self, host='localhost', port=8025,
                 mailboxFile=None, threadName=None):
        self.throwExceptionIfAddressIsInUse(host, port)
        self.initializeThread(threadName)
        self.initializeSmtpSinkServer(host, port, mailboxFile)

    def throwExceptionIfAddressIsInUse(self, host, port):
        """Assert that the port is available."""
        testSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        testSocket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR,
            testSocket.getsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR) | 1)
        testSocket.bind((host, port))
        testSocket.close()

    def initializeThread(self, threadName):
        """Initialize the server thread."""
        self._stopevent = threading.Event()
        self.threadName = threadName
        if self.threadName is None:
            self.threadName = SmtpSink.__class__
        threading.Thread.__init__(self, name=self.threadName)
        
    def initializeSmtpSinkServer(self, host, port, mailboxFile):
        """Initialize the SMTP server."""
        self.smtpSinkServer = SmtpSinkServer((host, port), None)
        self.resetMailbox(mailboxFile)
        smtpd.__version__ = SmtpSinkServer.__version__ 
                
    def resetMailbox(self, mailboxFile=None):
        """Set the Unix mailbox file object."""
        self.mailboxFile = mailboxFile
        if self.mailboxFile is None:
            self.mailboxFile = StringIO.StringIO()
        self.smtpSinkServer.setMailboxFile(self.mailboxFile)

    def getMailboxContents(self):
        """Get the contents of the mailbox file."""
        return self.mailboxFile.getvalue()
    
    def getMailboxFile(self):
        """Get the mailbox file object."""
        return self.mailboxFile
    
    def run(self):
        """Perform the thread operations."""
        while not self._stopevent.isSet():
            asyncore.loop(
                timeout=SmtpSink.SHUTDOWN_DELAY, count=1)

    def stop(self, timeout=None):
        """Shut down the server thread."""
        self._stopevent.set()
        threading.Thread.join(self, timeout)
        self.smtpSinkServer.close()
        
########################### end of file ##############################
