#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python


def make_process():
    import sys
    import threading
    import argparse
    import logging
    from os import environ

    parser = argparse.ArgumentParser(
        description="Interactive shell for malcolm")
    parser.add_argument(
        '--client', '-c',
        help="Add a client to given server, like ws://localhost:8080 or pva")
    parser.add_argument(
        '--log', default="INFO",
        help="Lowest level of logs to see. One of: ERROR, WARNING, INFO, DEBUG "
        "Default is INFO")
    parser.add_argument(
        'yaml', nargs="?",
        help="The YAML file containing the blocks to be loaded"
    )
    args = parser.parse_args()
    # assuming loglevel is bound to the string value obtained from the
    # command line argument. Convert to upper case to allow the user to
    # specify --log=DEBUG or --log=debug
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logging.basicConfig(level=numeric_level)

    from malcolm.core import SyncFactory, Process
    from malcolm.yamlutil import make_include_creator

    sf = SyncFactory("Sync")

    if args.yaml:
        proc_name = os.path.basename(args.yaml).split(".")[-2]
        proc = Process(proc_name, sf)
        with open(args.yaml) as f:
            assembly = make_include_creator(f.read())
        params = assembly.MethodMeta.prepare_input_map()
        assembly(proc, params)
        proc_name = "%s - imalcolm" % proc_name
    else:
        proc = Process("Process", sf)
        proc_name = "imalcolm"
    # set terminal title
    sys.stdout.write("\x1b]0;%s\x07" % proc_name)


    if args.client:
        if args.client.startswith("ws://"):
            from malcolm.comms.websocket import WebsocketClientComms
            hostname, port = args.client[5:].split(":")
            comms = WebsocketClientComms(
                proc, dict(hostname=hostname, port=int(port)))
            proc.add_comms(comms)

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "simple": {
                "format": "%(name)s: %(message)s"
            },
            "extended": {
                "format": "%(asctime)s - %(levelname)6s - %(name)s\n"
                          "    %(message)s"
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },

            # "local_file_handler": {
            #     "class": "logging.handlers.RotatingFileHandler",
            #     "level": "DEBUG",
            #     "formatter": "extended",
            #     "filename": "/tmp/debug.log",
            #     "maxBytes": 100048576,
            #     "backupCount": 4,
            #     "encoding": "utf8"
            # },

            "graylog_gelf": {
                "class": "pygelf.GelfTcpHandler",
                # Obviously a DLS-specific configuration: the graylog server
                # address and port
                "host": "graylog2.diamond.ac.uk",
                "port": 12202,
                "debug": True,
                "level": "DEBUG",
                #  The following custom fields will be disabled if setting this
                # False
                "include_extra_fields": True,
                "username": getpass.getuser(),
                "pid": os.getpid()
            }
        },


        # "loggers": {
        #     # Fine-grained logging configuration for individual modules or
        #     # classes
        #     # Use this to set different log levels without changing 'real' code.
        #     "myclasses": {
        #         "level": "DEBUG",
        #         "propagate": True
        #     },
        #     "usermessages": {
        #         "level": "INFO",
        #         "propagate": True,
        #         "handlers": ["console"]
        #     }
        # },

        "root": {
            "level": "DEBUG",
            "handlers": ["graylog_gelf", "console"],
        }
    }

    if args.logcfg:
        with open(args.logcfg) as f:
            text = f.read()
        if args.logcfg.endswith(".json"):
            file_config = json.loads(text)
        else:
            raise ValueError(
                "Don't know how to create client to %s" % args.client)

    def gui(block):
        global opener
        opener.open_gui(block, proc)

    try:
        environ['DISPLAY']
        # If this environment variable doesn't exist then there is probably no
        # X server for us to talk to.
    except KeyError:
        pass
    else:
        from PyQt4.Qt import QApplication

        # Start qt
        def start_qt():
            global app
            app = QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(False)
            from malcolm.gui.guiopener import GuiOpener
            global opener
            opener = GuiOpener()
            app.exec_()

        qt_thread = threading.Thread(target=start_qt)
        qt_thread.start()

    return proc, gui


def main():
    from malcolm.core.profilingsampler import ProfilingSampler
    sampler = ProfilingSampler()

    self, gui = make_process()

    header = """Welcome to iMalcolm.

self.process_block.blocks:
    %s

Try:
hello = self.get_block("HELLO")
print hello.greet("me")

or

gui(self.get_block("COUNTER"))

or

self.process_block.blocks
""" % (self.process_block.blocks,)

    self.start()

    # Temporary hack for I18 (should be handled by save/restore).
    self.get_block("I18-PANDA01-COUNTER1").outDatasetName = "Iref"
    self.get_block("I18-PANDA01-COUNTER2").outDatasetName = "I0"
    self.get_block("I18-PANDA01-COUNTER3").outDatasetName = "It"

    try:
        import IPython
    except ImportError:
        import code
        code.interact(header, local=locals())
    else:
        IPython.embed(header=header)
    global app
    app.quit()


if __name__ == "__main__":
    import os
    import sys

    os.environ["EPICS_CA_MAX_ARRAY_BYTES"] = "6000000"

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from pkg_resources import require

    sys.path.insert(0,
                    "/dls_sw/work/tools/RHEL6-x86_64/odin/venv/lib/python2.7/"
                    "site-packages")
    require("tornado", "numpy", "cothread", "ruamel.yaml",
            "scanpointgenerator", "h5py")
    #sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scanpointgenerator"))
    sys.path.append(
        "/dls_sw/work/R3.14.12.3/support/pvaPy/lib/python/2.7/linux-x86_64")

    main()
