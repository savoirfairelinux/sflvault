#!/usr/bin/python

import platform
if platform.system() != 'Windows':
    import pexpect
import os
from pprint import pprint
import pdb
from datetime import datetime
#import subprocess


class FishClient(object):
    """Fish protocol implementation, given a running SSH session
    in an pexpect spawn'd object.
    """
    
    def __init__(self, proc):
        """Init the class with the process. Start the session with .start()"""
        self.proc = proc

    def _wait_for(self, until):
        """Read lines until one starting with 'until', return read lines.
        """
        lines = []
        while True:
            # Add some handling to make it stop at some point..
            try:
                l = self.proc.readline()
            except KeyboardInterrupt, e:
                print "Before: ", self.proc.before
                print "After: ", self.proc.after
                print "Buffer: ", self.proc.buffer
                return (lines, 'KeyboardInterrupt')
            # Stop when starts with 'until'
            if l.startswith(until):
                return (lines, l)
            lines.append(l)


    def start(self):
        """Start the FISH connection, init and get the remote version if any
        """
        self.proc.sendline('#FISH')
        self.proc.sendline('echo; start_fish_server; echo "### 200"')
        lines, retval = self._wait_for('### 200')

        self.proc.sendline('#VER 0.0.2 <feature1> <feature2> <...>')
        self.proc.sendline("echo '### 000'")
        lines, retval = self._wait_for('###')

    def dele(self, filename):
        """Delete a remote file"""
        self.proc.sendline("#DELE %s" % filename)
        self.proc.sendline("rm -f %s 2>/dev/null" % filename)
        self.proc.sendline("echo '### 000'")
        lines, retval = self._wait_for('### 000')
        pprint((lines, retval))


    def retr(self, filename, write_to, callback=None):
        """Retrieve a file from remote host, and write the content to the
        given file-like object"""
        self.proc.sendline('''#RETR "%s"''' % (filename))
        self.proc.sendline("""ls -l "%s" | ( read a b c d x e; echo $x ); echo '### 100'; cat "%s"; echo '### 200'""" % (filename, filename))
        lines, retval = self._wait_for('### 100')
        filelen = int(lines.pop().strip())
        print filelen

        print "Downloading..."
        dl = 0
        remain = filelen
        self.callback_chk = -1
        while True:
            if callback:
                self.remain = remain
                self.filelen = filelen
                callback(self)

            # Less than one byte remaining (should always be zero btw)
            if remain < 1:
                break
            packsize = (4096 if remain > 4095 else remain % 4096)
            chunk = self.proc.read_nonblocking(packsize, timeout=None)
            # ttys always send \r\n even though the underlying program
            # sends a \n, that's why this mangling is necessary.
            chunk = chunk.replace("\r\n", "\n")
            remain -= len(chunk)
            # This if is necessary to catch \r\n splitted into two read() calls
            if chunk[-1:] == "\r":
                nextchr = self.proc.read_nonblocking(1, timeout=None)
                if nextchr == "\n":
                    chunk = chunk[:-1] + "\n"
                elif remain == 0:
                    self.proc.buffer = nextchr
                else:
                    remain -= 1
                    chunk += nextchr
            write_to.write(chunk)

        print "Download done."

        # Take out the CRLF chars produced by cat.
        #self.proc.read(2)

        lines, retval = self._wait_for('### 200')

    def stor(self, remote_filename, read_from, filelen, callback=None):
        """Store a file to remote host, reading from read_form.read()"""
        olddelay = self.proc.delaybeforesend

        # Taken from lftp's fish.c implementation
              
        cmd = """#STOR %lu "%s"\n""" % (filelen, remote_filename)
        cmd += """stty -echo; rest=%lu;file="%s";:>$file;echo '### 001';""" % (filelen,remote_filename)
        cmd += "stty -icanon;"
        cmd += "if echo 1|head -c 1 -q ->/dev/null 2>&1;then "
        cmd += "head -c $rest -q -|(cat>$file;cat>/dev/null);"
        cmd += "else while [ $rest -gt 0 ];do "
        cmd += "bs=4096;cnt=`expr $rest / $bs`;"
        cmd += "[ $cnt -eq 0 ] && { cnt=1;bs=$rest; }; "
        cmd += "n=`dd ibs=$bs count=$cnt 2>/dev/null|tee -a $file|wc -c`;"
        cmd += "[ \"$n\" -le 0 ] && exit;"
        cmd += "rest=`expr $rest - $n`; "
        cmd += "done;fi;stty icanon;stty echo;echo '### 200'\n"

        cmd2 = """#STOR %lu "%s"
              echo '### 001'
              {
                     stty -echo
                     file="%s"
                     rest=%lu
                     while [ $rest -gt 0 ]
                     do
                         cnt=`expr \\( $rest + 255 \\) / 256`
                         n=`dd bs=256 count=$cnt 2> /dev/null | tee -a "$file" | wc -c`
                         rest=`expr $rest - $n`
                     done
                     stty echo
              }
              echo '### 200'\n""" % (filelen, remote_filename,
                                        remote_filename, filelen)


        self.proc.send(cmd)
        lines, retval = self._wait_for('### 001')

        # Write:
        print "Uploading..."
        self.proc.delaybeforesend = 0
        dl = 0
        remain = filelen
        self.callback_chk = -1
        while True:
            if callback:
                self.remain = remain
                self.filelen = filelen
                callback(self)

            # Less than one byte remaining (should always be zero btw)
            if remain < 1:
                break
            packsize = (4096 if remain > 4095 else remain % 4096)
            chunk = read_from.read(packsize)
            remain -= len(chunk)
            os.write(self.proc.child_fd, chunk)

        self.proc.delaybeforesend = olddelay
        lines, retval = self._wait_for('### 200')
        print "Uploading done."

def showstatus(fishproc):
    n = datetime.now().second
    if fishproc.callback_chk != n:
        fishproc.callback_chk = n
        diff = fishproc.filelen - fishproc.remain
        print "%d / %d" % (diff, fishproc.filelen)

if __name__ == '__main__':
    # Connect to an ssh command
    proc = pexpect.spawn('ssh office')

    # Create the FishClient and wrap it around.
    # This can also be done after the interact() session if you wish.
    fc = FishClient(proc)
    
    # Set the escape character to what you want.
    proc.interact(escape_character=chr(30))
    
    # Automatically start the Fish session when escaping.
    fc.start()

    oldn = -1

    fname = '/tmp/' + raw_input("Fichier dans /tmp/: ")
    filesize = os.path.getsize(fname)
    myfile = open(fname, 'rb')
    fc.stor(fname, myfile, filesize, showstatus)
    myfile.close()

    proc.interact()

    print "Closing connection"
    proc.close()

