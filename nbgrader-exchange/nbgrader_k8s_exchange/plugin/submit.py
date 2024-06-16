import base64
import os
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH, S_ISGID
)
from textwrap import dedent

from nbgrader.exchange.abc import ExchangeSubmit as ABCExchangeSubmit
from traitlets import Bool

from .exchange import Exchange
from nbgrader.utils import get_username, check_mode, find_all_notebooks

import requests
from requests.exceptions import HTTPError


class ExchangeSubmit(Exchange, ABCExchangeSubmit):

    add_random_string = Bool(
        True,
        help=dedent(
            "Whether to add a random string on the end of the submission."
        )
    ).tag(config=True)

    def init_src(self):
        if self.path_includes_course:
            root = os.path.join(self.coursedir.course_id, self.coursedir.assignment_id)
            other_path = os.path.join(self.coursedir.course_id, "*")
        else:
            root = self.coursedir.assignment_id
            other_path = "*"
        self.src_path = os.path.abspath(os.path.join(self.assignment_dir, root))
        self.coursedir.assignment_id = os.path.split(self.src_path)[-1]
        if not os.path.isdir(self.src_path):
            self._assignment_not_found(self.src_path, os.path.abspath(other_path))

    def init_dest(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")
        if not self.authenticator.has_access(self.coursedir.student_id, self.coursedir.course_id):
            self.fail("You do not have access to this course.")

        self.cache_path = os.path.join(self.cache, self.coursedir.course_id)
        if self.coursedir.student_id != '*':
            # An explicit student id has been specified on the command line; we use it as student_id
            if '*' in self.coursedir.student_id or '+' in self.coursedir.student_id:
                self.fail("The student ID should contain no '*' nor '+'; got {}".format(self.coursedir.student_id))
            self.student_id = self.coursedir.student_id
        else:
            self.student_id = get_username()

        self.inbound_path = os.path.join(self.root, self.coursedir.course_id, 'inbound', self.student_id)
        self.ensure_directory(
            self.inbound_path,
            S_ISGID|S_IRUSR|S_IWUSR|S_IXUSR|S_IWGRP|S_IXGRP|S_IWOTH|S_IXOTH|(S_IRGRP if self.coursedir.groupshared else 0)
        )

        if self.add_random_string:
            random_str = base64.urlsafe_b64encode(os.urandom(9)).decode('ascii')
            self.assignment_filename = '{}+{}+{}+{}'.format(
                self.student_id, self.coursedir.assignment_id, self.timestamp, random_str)
        else:
            self.assignment_filename = '{}+{}+{}'.format(
                self.student_id, self.coursedir.assignment_id, self.timestamp)

    def init_release(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        course_path = os.path.join(self.root, self.coursedir.course_id)
        outbound_path = os.path.join(course_path, 'outbound')
        self.release_path = os.path.join(outbound_path, self.coursedir.assignment_id)
        if not os.path.isdir(self.release_path):
            self.fail("Assignment not found: {}".format(self.release_path))
        if not check_mode(self.release_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.release_path))

    def check_filename_diff(self):
        released_notebooks = find_all_notebooks(self.release_path)
        submitted_notebooks = find_all_notebooks(self.src_path)

        # Look for missing notebooks in submitted notebooks
        missing = False
        release_diff = list()
        for filename in released_notebooks:
            if filename in submitted_notebooks:
                release_diff.append("{}: {}".format(filename, 'FOUND'))
            else:
                missing = True
                release_diff.append("{}: {}".format(filename, 'MISSING'))

        # Look for extra notebooks in submitted notebooks
        extra = False
        submitted_diff = list()
        for filename in submitted_notebooks:
            if filename in released_notebooks:
                submitted_diff.append("{}: {}".format(filename, 'OK'))
            else:
                extra = True
                submitted_diff.append("{}: {}".format(filename, 'EXTRA'))

        if missing or extra:
            diff_msg = (
                "Expected:\n\t{}\nSubmitted:\n\t{}".format(
                    '\n\t'.join(release_diff),
                    '\n\t'.join(submitted_diff),
                )
            )
            if missing and self.strict:
                self.fail(
                    "Assignment {} not submitted. "
                    "There are missing notebooks for the submission:\n{}"
                    "".format(self.coursedir.assignment_id, diff_msg)
                )
            else:
                self.log.warning(
                    "Possible missing notebooks and/or extra notebooks "
                    "submitted for assignment {}:\n{}"
                    "".format(self.coursedir.assignment_id, diff_msg)
                )

    def copy_files(self):
        self.init_release()

        dest_path = os.path.join(self.inbound_path, self.assignment_filename)
        if self.add_random_string:
            cache_path = os.path.join(self.cache_path, self.assignment_filename.rsplit('+', 1)[0])
        else:
            cache_path = os.path.join(self.cache_path, self.assignment_filename)

        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(dest_path))

        # copy to the real location
        self.check_filename_diff()
        self.do_copy(self.src_path, dest_path)
        with open(os.path.join(dest_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)
        self.set_perms(
            dest_path,
            fileperms=(S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH),
            dirperms=(S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH))

        # Make this 0777=ugo=rwx so the instructor can delete later. Hidden from other users by the timestamp.
        os.chmod(
            dest_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IWGRP|S_IXGRP|S_IROTH|S_IWOTH|S_IXOTH
        )

        # also copy to the cache
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        self.do_copy(self.src_path, cache_path)
        with open(os.path.join(cache_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)

        self.log.info("Submitted as: {} {} {}".format(
            self.coursedir.course_id, self.coursedir.assignment_id, str(self.timestamp)
        ))

        manager_url = "http://manager:8080"
        # call collect via manager
        collect_url = manager_url + f"/collect/{self.coursedir.course_id}/{self.coursedir.assignment_id}"

        try:
            response = requests.post(collect_url)
            response.raise_for_status()
        except HTTPError as http_err:
            self.log.error(f"HTTP error occurred in accessing manager: {http_err}")
        except Exception as err:
            self.log.error(f"Other error occurred in accessing manager: {err}")
        else:
            json_response = response.json()
            if json_response['success']:
                self.log.info(json_response["log"])
            else: 
                self.log.error(json_response["log"])

        # call autograde via manager
        autograde_url = manager_url + f"/autograde/{self.coursedir.course_id}/{self.coursedir.assignment_id}/{self.student_id}"

        try:
            response = requests.post(autograde_url)
            response.raise_for_status()
        except HTTPError as http_err:
            self.log.error(f"HTTP error occurred in accessing manager: {http_err}")
        except Exception as err:
            self.log.error(f"Other error occurred in accessing manager: {err}")
        else:
            json_response = response.json()
            if json_response['success']:
                self.log.info(json_response["log"])
            else: 
                self.log.error(json_response["log"])

        # call checker via manager
        checker_url = manager_url + f"/send_checker/{self.coursedir.course_id}/{self.coursedir.assignment_id}/{self.student_id}"

        try:
            response = requests.post(checker_url)
            response.raise_for_status()
        except HTTPError as http_err:
            self.log.error(f"HTTP error occurred in accessing manager: {http_err}")
        except Exception as err:
            self.log.error(f"Other error occurred in accessing manager: {err}")
        else:
            json_response = response.json()
            if json_response['success']:
                self.log.info(json_response["log"])
            else: 
                self.log.error(json_response["log"])
