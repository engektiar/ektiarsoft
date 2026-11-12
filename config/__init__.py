# Use PyMySQL as a drop-in MySQLdb replacement (no C compiler needed on Windows/XAMPP).
try:
    import pymysql

    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
