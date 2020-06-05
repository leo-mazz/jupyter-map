from IPython.display import display
import ipywidgets as widgets
import pandas as pd
import gmaps
import numpy as np

class Heatmap(object):
    """
    Jupyter widget for exploring the funding distribution across the UK per year.
    Additionally has options to display funding for all years and to normalise funding
    per capita
    """

    def __init__(self, latitudes, longitudes, dates, weights, norms, center=[54, 0], zoom=6):
        """
        Input pandas.DataFrame. Must have the following fields:
            funding_amount
            lat_coordinate
            lon_coordinate
            funding_per_capita
            year - needs to be a 4 letter string
        """
        self.center = center
        self.zoom = zoom
        self.latitudes = latitudes
        self.longitudes = longitudes
        self.coordinates = np.stack([self.latitudes, self.longitudes]).T
        self.dates = dates
        self.weights = weights / weights.max()
        self.norm_weights = weights * norms
        self.norm_weights = self.norm_weights / self.norm_weights.max()
        self.slider = None
        self.norm_val = False
        initial_date = self.dates.min()

        map_figure = self.render_map(initial_date)
        controls = self.render_controls(initial_date)
        self._container = widgets.VBox([controls, map_figure])

        self.render()

    def render(self):
        display(self._container)

    def on_year_change(self, change):
        """Change data to be displayed based on the year selected"""
        date = self.slider.value
        relevant_ix = self.locations_for_date(date)
        self.heatmap.locations = self.coordinates[relevant_ix]
        if self.norm_val:
            self.heatmap.weights = self.norm_weights[relevant_ix]
        else:
            self.heatmap.weights = self.weights[relevant_ix]
        return self._container

    def toggle_all_dates(self, b):
        self.heatmap.locations = self.coordinates
        if self.norm_val:
            self.heatmap.weights = self.norm_weights
        else:
            self.heatmap.weights = self.weights
        return self._container

    def normalize(self, value):
        if value['name'] == 'value':
            self.norm_val = value['new']
            if value['new']:
                self.heatmap.weights = self.norm_weights
            else:
                self.heatmap.weights = self.weights
            return self._container

    def render_map(self, initial_date):
        fig = gmaps.figure(map_type='HYBRID', layout={'width': '1000px',
                                                      'height': '800px'}, zoom_level=self.zoom, center=self.center)
        relevant_ix = self.locations_for_date(initial_date)
        self.heatmap = gmaps.heatmap_layer(self.coordinates[relevant_ix],
                                           weights=self.weights[relevant_ix],
                                           max_intensity=20.0)
        fig.add_layer(self.heatmap)
        return fig

    def render_controls(self, initial_date):
        self.slider = widgets.IntSlider(
            value=initial_date,
            min=self.dates.min(),
            max=self.dates.max(),
            description='Date',
            continuous_update=False)
        self.slider.observe(self.on_year_change, names='value')

        self._all_dates_button = widgets.Button(description="All dates")
        self._all_dates_button.on_click(self.toggle_all_dates)

        self._norm_capita_checkbox = widgets.Checkbox(
            value=False,
            description='Normalize',
            disabled=False,
            indent=False)
        self._norm_capita_checkbox.observe(self.normalize)

        controls = widgets.HBox(
            [self._all_dates_button, self.slider, self._norm_capita_checkbox],
            layout={'justify_content': 'space-between'}
        )
        return controls

    def locations_for_date(self, date):
        """Get dataset only for the selected year"""
        return self.dates == date
