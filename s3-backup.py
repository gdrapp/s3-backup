import tarfile
import yaml
import datetime
import logging
import argparse
import re
import sys
import tempfile
from s3bucket import S3Bucket, S3BucketError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig()


class TarFileCreationError(Exception):
    pass


class ConfigError(Exception):
    pass


class TarFilter:
    def __init__(self, exclusions: list):
        self.regexes = [re.compile(e) for e in exclusions]

    def filter(self, tarinfo: tarfile.TarInfo):
        if not tarinfo.isfile():
            return tarinfo

        for regex in self.regexes:
            if regex.search(tarinfo.name) is not None:
                logger.debug(f"Excluding file {tarinfo.name}")
                return None

        logger.debug(f"Adding file to tarball: {tarinfo.name}")
        return tarinfo


def read_config(config_file: str):
    config = None
    logger.info(f"Reading config from file: {config_file}")

    try:
        file = open(config_file, "r")
    except IOError as e:
        raise ConfigError("Error reading config file") from e
    else:
        with file as stream:
            try:
                config = yaml.safe_load(stream)
                return config
            except yaml.YAMLError as e:
                raise ConfigError("Error reading configuration") from e


def create_tarfile(fileobj, contents: list, exclusions: list = None):
    try:
        file = tarfile.open(fileobj=fileobj, mode="w:gz")
    except FileExistsError as e:
        raise TarFileCreationError(
            f"Unable to create tar file {filename}, it already exists") from e
    except tarfile.CompressionError as e:
        raise TarFileCreationError("Compression method not available") from e
    else:
        tarfilter = TarFilter(exclusions)

        for item in contents:
            try:
                logger.debug(f"Adding object to tarball: {item}")
                file.add(item, filter=tarfilter.filter)
            except tarfile.TarError as e:
                logger.error(f"Error adding file to tarball: {e}")

        logger.debug("Closing tar file")
        file.close()


def create_tempfile():
    logger.debug(f"Creating temporary file")
    return tempfile.TemporaryFile()


def generate_s3_key(prefix: str):
    timestr = datetime.datetime.now().strftime(r"%Y%m%dT%H%M%S")
    return prefix + timestr + ".tar.gz"


def main():
    parser = argparse.ArgumentParser(description='Amazon S3 Backup.')
    parser.add_argument('config_file', help='JSON configuration file')
    args = parser.parse_args()

    try:
        config = read_config(args.config_file)
    except ConfigError as e:
        logger.exception("Error reading configuration file")
        sys.exit(1)

    logger.debug(config)

    logger.debug("Creating temporary tar file")
    tempfile = create_tempfile()

    try:
        create_tarfile(tempfile, config.get(
            "sources"), config.get("exclusions"))
    except TarFileCreationError as e:
        logger.error(f"Error creating tar file: {e}")
        sys.exit(1)

    tempfile.seek(0)  # Needed for S3 upload to work

    logger.debug("Creating S3 bucket object")
    s3_bucket = S3Bucket(config.get("s3").get("bucket_name"),
                         config.get("s3").get("bucket_region"), config.get("s3").get("storage_class"))

    s3_metadata = {"sources": ",".join(config.get("sources")),
                   "exclusions": ",".join(config.get("exclusions"))}
    s3_key = generate_s3_key(config.get("tarfile_name_prefix"))

    logger.info("Uploading file to S3")
    s3_bucket.upload_fileobj(tempfile, s3_key, s3_metadata)

    logger.debug("Closing temporary tar file")
    tempfile.close()

    logger.info("Done!")


if __name__ == "__main__":
    main()
