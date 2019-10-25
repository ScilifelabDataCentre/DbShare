# Tutorial: Chart

- A chart can be created from a table or a view: Click **Chart** in the
  table/view page.
- The **Select chart** page shows which chart templates can be matched with the
  source table/view. This depends on the chart templates available, and
  on the schema of the table/view.
- Clicking one of the options shows the different possible permutations
  of mapping the columns of the table/view to the visual channels of the
  chart.
- Click **Render** the select a permutation.
- The new page shows the chart, and allows updating some parameters of
  the chart.
- Click **Save** to save the chart as it is. It will show up in the database
  page, and in the page of the source table/view.
- NOTE: A chart is rendered anew each time the page is accessed. This means
  that if the source table/view is changed, the chart will reflect this
  change once its page is rendered again.
- Saved charts are deleted when the source table/view is deleted.

### Vega-Lite

- [Vega-Lite](https://vega.github.io/vega-lite/) is a declarative visualization
  specification language.
- The current Vega-Lite templates in DbShare only use a very small subset
  of the feature of Vega-Lite.
- It is possible to edit the Vega-Lite code for a chart to leverage more of the
  Vega-Lite features, but this requires expertise by the user.
