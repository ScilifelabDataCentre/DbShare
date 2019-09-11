"Test the chart API endpoint."

import csv
import io
import http.client

import base


class Chart(base.Base):
    "Test the chart API endpoint."

    table_spec = {
        'name': 't1',
        'title': 'Test table',
        'columns': [
            {'name': 'i',
             'type': 'INTEGER',
             'primarykey': True},
            {'name': 't',
             'type': 'TEXT',
             'notnull': False},
            {'name': 'r',
             'type': 'REAL',
             'notnull': True}
        ]
    }

    def get_csvfile_data(self, rows):
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow([c['name'] for c in self.table_spec['columns']])
        writer.writerows(rows)
        return csvfile.getvalue()

    def test_table(self):
        "Create a database and table, and a chart for it."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)

        # Insert CSV data.
        headers = {'Content-Type': 'text/csv'}
        url = self.root['operations']['table']['insert']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        data = self.get_csvfile_data([(1, 'class1', 4.5),
                                      (2, 'class2', 2.1),
                                      (3, 'class2', 8.5),
                                      (4, 'class3', -1.3)])
        response = self.session.post(url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 4)

        # Create the chart from the stencil 'scatterplot_color'
        data = {'sourcename': self.table_spec['name'],
                'stencilname': 'scatterplot_color',
                'title': 'Testing chart',
                'width': 600,
                'height': 600,
                'x': 'i',
                'y': 'r',
                'color': 't'}
        CHARTNAME = 'testchart'
        url = self.root['operations']['chart']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         chartname=CHARTNAME)
        response = self.session.put(url, json=data)
        result = self.check_schema(response)
        chart_url = response.url

        # Attempt to create chart with same name should fail.
        response = self.session.put(url, json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Delete the table.
        url = self.root['operations']['table']['delete']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # The chart should now be gone.
        response = self.session.get(chart_url)
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_view(self):
        "Create a database, table and view, and a chart for it."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)

        # Insert CSV data.
        headers = {'Content-Type': 'text/csv'}
        url = self.root['operations']['table']['insert']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        data = self.get_csvfile_data([(1, 'class1', 4.5),
                                      (2, 'class2', 2.1),
                                      (3, 'class2', 8.5),
                                      (4, 'class3', -1.3)])
        response = self.session.post(url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 4)

        # Create the view of the table.
        VIEWNAME = 'v1'
        view_spec = {
            'name': VIEWNAME,
            'query': {'from': self.table_spec['name'],
                      'select': 'i, t, r',
                      'where': 'r<8'}
        }
        url = self.root['operations']['view']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         viewname=view_spec['name'])
        response = self.session.put(url, json=view_spec)
        result = self.check_schema(response)

        # Create the chart from the stencil 'scatterplot_color'
        data = {'sourcename': VIEWNAME,
                'stencilname': 'scatterplot_color',
                'title': 'Testing chart of view',
                'width': 600,
                'height': 600,
                'x': 'i',
                'y': 'r',
                'color': 't'}
        CHARTNAME = 'testchart2'
        url = self.root['operations']['chart']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         chartname=CHARTNAME)
        response = self.session.put(url, json=data)
        result = self.check_schema(response)

        # Delete the table.
        url = self.root['operations']['table']['delete']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    base.run()
