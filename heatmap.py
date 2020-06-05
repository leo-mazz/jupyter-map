from IPython.display import display
import ipywidgets as widgets
import pandas as pd
import gmaps
import numpy as np

class Heatmap(object):
    """
    A heat map widget for Jupyter notebooks that interfaces with Google Maps. It expects data in a numpy array. Weights are used for the heat in the map and norms for normalizing (e.g. by population).
    """

    def __init__(self, latitudes, longitudes, dates, weights, norms, center=[54, 0], zoom=6):
        self.center = center
        self.zoom = zoom
        self.latitudes = latitudes
        self.longitudes = longitudes
        self.coordinates = np.stack([self.latitudes, self.longitudes]).T
        self.dates = dates
        self.weights = weights / weights.max()
        self.norm_weights = weights * norms
        self.norm_weights = self.norm_weights / self.norm_weights.max()
        self.norm_val = False
        initial_date = self.dates.min()

        map_figure = self.render_map(initial_date)
        controls = self.render_controls(initial_date)
        self._container = widgets.VBox([controls, map_figure])

        self.render()

    def render(self):
        display(self._container)

    def on_date_change(self, change):
        date = self._slider.value
        relevant_ix = self.locations_for_date(date)
        self.heatmap.locations = self.coordinates[relevant_ix]
        self.update_norms(relevant_ix)
        return self._container

    def toggle_all_dates(self, b):
        self.heatmap.locations = self.coordinates
        self.update_norms()
        return self._container
    
    def update_norms(self, relevant_ix=None):
        if relevant_ix is None:
            relevant_ix = np.ones(len(self.weights))

        if self.norm_val:
            self.heatmap.weights = self.norm_weights
        else:
            self.heatmap.weights = self.weights

    def normalize(self, value):
        if value['name'] == 'value':
            self.norm_val = value['new']
            self.update_norms()
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
        self._slider = widgets.IntSlider(
            value=initial_date,
            min=self.dates.min(),
            max=self.dates.max(),
            description='Date',
            continuous_update=False)
        self._slider.observe(self.on_date_change, names='value')

        self._all_dates_button = widgets.Button(description="All dates")
        self._all_dates_button.on_click(self.toggle_all_dates)

        self._norm_capita_checkbox = widgets.Checkbox(
            value=False,
            description='Normalize',
            disabled=False,
            indent=False)
        self._norm_capita_checkbox.observe(self.normalize)

        controls = widgets.HBox(
            [self._all_dates_button, self._slider, self._norm_capita_checkbox],
            layout={'justify_content': 'space-between'}
        )
        return controls

    def locations_for_date(self, date):
        return self.dates == date
