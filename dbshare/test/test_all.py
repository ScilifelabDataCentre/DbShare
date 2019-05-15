"Run all tests."

import unittest

from dbshare.test.test_root import Root
from dbshare.test.test_user import User
from dbshare.test.test_dbs import Dbs
from dbshare.test.test_db import Db


if __name__ == '__main__':
    unittest.main()
