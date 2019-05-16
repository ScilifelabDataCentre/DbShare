"Run all tests."

import unittest

from dbshare.test.root import Root
from dbshare.test.user import User
from dbshare.test.dbs import Dbs
from dbshare.test.db import Db
from dbshare.test.table import Table
from dbshare.test.query import Query
from dbshare.test.view import View


if __name__ == '__main__':
    unittest.main()
