import smtplib, StringIO, mailbox, email
from smtpsink import SmtpSink

smtpSink = SmtpSink(port=1025)
smtpSink.start()

data = '''From: source@domain.com
To: dest@domain.com
Subject: Hello World

This is the message.
'''

sender = smtplib.SMTP('localhost', 1025)
sender.set_debuglevel(1)
sender.sendmail('source@domain.com', ['dest@domain.com'], data)
sender.quit()

smtpSink.stop()

mailboxFile =  StringIO.StringIO(smtpSink.getMailboxContents())
mailboxObject = mailbox.PortableUnixMailbox(
    mailboxFile, email.message_from_file)
for messageText in [ message.as_string() for message in mailboxObject ]:
    print 'Header:'
    print 'To: {}\nFrom: {}\n'.format(
        message.get('To'), message.get('From'))
    print 'Message Text:'
    print messageText
