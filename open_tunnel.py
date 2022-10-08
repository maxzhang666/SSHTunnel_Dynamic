import asyncio
import io
import logging
import os.path
import sys

import asyncssh
import errno
import socket
import threading
import time

# Logger
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

### Setup the console handler with a StringIO object
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.ERROR)

### Add the console handler to the logger
logger.addHandler(ch)

logger.info("Logger set!")

logger.info("SSH Tunnel starting...")


class OpenSSH:
    def __init__(self, host, username, password, port, keys, known_hosts=None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.known_hosts = known_hosts
        self.conn = None
        self.ssh_status = None
        self.keys = keys

    async def run_client(self, stop):

        async with asyncssh.connect(
                host=self.host,
                username=self.username,
                password=self.password,
                known_hosts=self.known_hosts,
                client_keys=self.keys if self.keys is not None else None
                # para
        ) as conn:
            # self.conn = conn
            listener = await conn.forward_socks('0.0.0.0', self.port)
            # self.ee.emit('msg', conn)
            logging.info('Listening on port %s...' % listener.get_port())
            self.ssh_status = True
            # time.sleep(5)
            # print(i, 'Listening on port %s...' % listener.get_port())

            while not stop():
                await asyncio.sleep(0.1)
                await listener.wait_closed()
            # await asyncio.sleep(30)
            conn.close()
            await listener.wait_closed()
            logging.info('SSH is Stoped')

    def thr(self, stop):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_client(stop))
        except (OSError, asyncssh.Error) as exc:
            self.ssh_status = False
            loop.close()
            logging.info('SSH connection failed: ' + str(exc))

    def waitResult(self):
        while self.ssh_status is None:
            time.sleep(0.1)
        return self.ssh_status


class SSHProxyControler:
    def __init__(self, host, username, password, port, client_key=None, known_hosts=None, port_retry=100, stop_thread=False):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.known_hosts = known_hosts
        self.stop_thread = stop_thread
        self.port_retry = port_retry
        self.keys = None

        if client_key is not None:
            if os.path.exists(client_key):
                self.keys = asyncssh.read_private_key(client_key)
                self.password = None
            else:
                logging.info('The Client Key File Is Not Found')

    def start(self):
        while True:
            if self.port_retry != 0:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.bind(("0.0.0.0", self.port))
                except socket.error as e:
                    if e.errno == errno.EADDRINUSE:
                        self.port += 1
                        self.port_retry -= 1
                    else:
                        return False, self.host, self.port
                s.close()
                break
            else:
                return False, self.host, self.port

        myssh = OpenSSH(self.host, self.username, self.password, self.port, self.keys)
        t1 = threading.Thread(target=myssh.thr, args=(lambda: self.stop_thread,))
        # t1.daemon = True
        t1.start()
        return t1, myssh.waitResult(), self.host, self.port

    def stop(self):
        self.stop_thread = True


def buildTunnel(host, username, password, port, key=None):
    controlssh = SSHProxyControler(host, username, password, port, key)
    t1, sshstatus, host, port = controlssh.start()
    logging.info("conn {},{},local bind :{}".format('success' if sshstatus else 'fail', host, port))
    if sshstatus:
        # time.sleep(30)
        # controlssh.stop()
        logger.info('SSH is Start')
    else:
        logger.info('Can not connect to SSH')
        controlssh.stop()
        sys.exit()


if __name__ == '__main__':
    ssh_host = os.environ.get('ssh_host')
    ssh_user = os.environ.get('ssh_user')
    ssh_pass = os.environ.get('ssh_pass')
    ssh_private_key = os.environ.get('ssh_private_key')
    ssh_local_port = os.environ.get('ssh_local_port')
    buildTunnel(ssh_host, ssh_user, ssh_pass, int(ssh_local_port), ssh_private_key)
