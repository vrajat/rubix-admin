import logging

from fabric.operations import sudo, put, os
from fabric.contrib.files import append
from fabric.state import env
from fabric.tasks import execute
from fabric.utils import abort


class Installer:
    @classmethod
    def setup_parsers(cls, sub_parser):
        cls.parser = sub_parser.add_parser("installer",
                                           help="Qubole Rubix Installer")

        cls.sub_parser = cls.parser.add_subparsers()

        cls.install_parser = cls.sub_parser.add_parser("install",
                                                       help="Install from RPM")
        cls.install_parser.add_argument("-r", "--rpm", required=True,
                                        help="Path to RPM file")
        cls.install_parser.add_argument("-a", "--rpm-args", default="--ignoreos",
                                        help="Arguments to rpm command")
        cls.install_parser.set_defaults(func=cls.install_cmd)

    @classmethod
    def install_cmd(cls, args):
        return execute(cls.install, args, hosts=args.config["hosts"])

    @classmethod
    def install(cls, args):
        cls._scp(args)
        cls._rpm_install(args)

    @classmethod
    def _scp(cls, args):
        remote_packages_path = args.config["remote_packages_path"]
        if not os.path.isfile(args.rpm):
            abort('RPM file not found at %s.' % args.rpm)

        logging.info("Deploying rpm on %s" % env.host)
        sudo('mkdir -p ' + remote_packages_path)
        ret_list = put(args.rpm, remote_packages_path, use_sudo=True)
        if not ret_list.succeeded:
            logging.warn("Failure during put. Now using /tmp as temp dir")
            ret_list = put(args.rpm, remote_packages_path,
                           use_sudo=True, temp_dir='/tmp')
        if ret_list.succeeded:
            logging.info("Package deployed successfully on: %s " % env.host)

    @classmethod
    def _rpm_install(cls, args):
            logging.warn("in rpm install")
        rpm_output = sudo('rpm -U %s %s' %
                    (args.rpm_args,
                     os.path.join(args.config["remote_packages_path"],
                                  os.path.basename(args.rpm))))

        sudo("cp -a /usr/lib/rubix/lib/* /usr/lib/presto/lib/plugin/hive-hadoop2/")
        sudo("cp -a /usr/lib/rubix/lib/* /usr/lib/hadoop/lib/")
        sudo("mkdir -p /media/ephemeral0")

        append("/usr/lib/presto/etc/catalog/hive.properties","hive.fs.s3n.impl=com.qubole.rubix.presto.CachingPrestoS3FileSystem", True)
        append("/usr/lib/presto/etc/catalog/hive.properties","hive.fs.s3.impl=com.qubole.rubix.presto.CachingPrestoS3FileSystem", True)
        append("/usr/lib/presto/etc/catalog/hive.properties","hive.fs.s3a.impl=com.qubole.rubix.presto.CachingPrestoS3FileSystem", True)