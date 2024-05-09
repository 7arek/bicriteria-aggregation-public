import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon
import numpy as np
import os


def plotGeo(ids=None,ax = None, reload=False):
    global gdf_shapefile, df_outer, tri_fill, tri_border
    # Step 1: Read the shapefile using geopandas
    if not reload:
        shapefile_path = "shape/osterloh.shp"
        gdf_shapefile = gpd.read_file(shapefile_path)

    # Step 2: Read and parse your custom file format
    if not reload:
        custom_file_path = "outer.txt"
        df_outer = pd.read_csv(custom_file_path,delimiter=";")

    # Filter the custom polygons by their IDs if specified
    df_filtered = df_outer
    if ids is not None:
        df_filtered = df_outer[df_outer['id'].isin(ids)]

    # Parse the polygons and create Shapely Polygon objects
    polygons = []
    for polygon_str in df_filtered['geometry']:
        polygon_coords = [tuple(map(float, point.split())) for point in polygon_str.replace('POLYGON ((', '').replace('))', '').split(', ')]
        polygon = Polygon(polygon_coords)
        polygons.append(polygon)

    gdf_custom = gpd.GeoDataFrame(df_filtered, geometry=polygons)

    if ax is None:
        fig, ax = plt.subplots()

    if reload:
        ax.clear()

    gdf_shapefile.plot(ax=ax, color='grey', edgecolor='black')


    gdf_custom.plot(ax=ax, color='grey',alpha=0.3)
    gdf_custom.boundary.plot(ax=ax, color='red', linewidth=0.3,alpha=0.3)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title('Geodata')
    if ax is None:
        plt.axis('off')
        plt.show()


def plotInteractive(fig,ax_scatter, ax_geo):
    global highlighted_point 
    highlighted_point = None
    df = pd.read_csv("solutions_labeled.csv", delimiter=",")

    extreme = df[df["extreme"] == True][["area","perimeter"]]
    nonextreme = df[df["extreme"] == False][["area","perimeter"]]

    ax_scatter.scatter(nonextreme["area"], nonextreme["perimeter"], c='lightblue', label='Non-Extreme points',s=1,alpha=0.5)
    ax_scatter.scatter(extreme["area"], extreme["perimeter"], c='orange', label='Extreme points',s=1*15,marker='s',alpha=0.5)

    # plt.plot(extreme["area"], extreme["perimeter"], c='orange', alpha=0.5,label='Convex Hull of Pareto-frontier')

    ax_scatter.legend()

    ax_scatter.set_xlabel('Area')
    ax_scatter.set_ylabel('Perimeter')

    data = df.to_numpy()
    for i in range(len(data)):
        data[i,2] = np.fromstring(data[i,2][1:-1],dtype=int,sep=",")
    
    def clear_highlight():
        global highlighted_point 
        if highlighted_point is not None: 
            highlighted_point.remove()
            highlighted_point = None

    def find_closest_point(x, y, data, ratio):
        distances = ((data[:, 0] - x) * ratio) ** 2 + (data[:, 1] - y) ** 2
    
        closest_index = np.argmin(distances)

        return data[closest_index]



    def on_scroll(event):
        if event.inaxes != ax_scatter or event.button != 'up' and event.button != 'down':
            return
        x_mouse = event.xdata
        y_mouse = event.ydata
        x_range_old = ax_scatter.get_xlim()[1] - ax_scatter.get_xlim()[0]
        y_range_old = ax_scatter.get_ylim()[1] - ax_scatter.get_ylim()[0]
        if event.button == 'up':
            scale_factor = 0.7
        elif event.button == 'down':
            scale_factor = 1.3
        new_x_range = x_range_old * scale_factor
        new_y_range = y_range_old * scale_factor
        x_new_min = x_mouse - (x_mouse - ax_scatter.get_xlim()[0]) * (new_x_range / x_range_old)
        x_new_max = x_new_min + new_x_range
        y_new_min = y_mouse - (y_mouse - ax_scatter.get_ylim()[0]) * (new_y_range / y_range_old)
        y_new_max = y_new_min + new_y_range
        ax_scatter.set_xlim(x_new_min, x_new_max)
        ax_scatter.set_ylim(y_new_min, y_new_max)
        plt.draw()


    def on_click(event):
        global highlighted_point 
        if event.inaxes != ax_scatter or event.button != 3 and event.button !=1:  # Check if right mouse button is clicked
            return
        x, y = event.xdata, event.ydata

        ratio = ax_scatter.get_data_ratio()
    
        if event.button == 3:
            closest_row = find_closest_point(x, y, data[data[:,3]==True],ratio)
        elif event.button == 1:
            closest_row = find_closest_point(x, y, data[data[:,3]==False],ratio)

        # scatter highlight
        clear_highlight() 
        highlighted_point = ax_scatter.scatter(closest_row[0], closest_row[1], color='red',marker="x", zorder=10,s=100,label="Visualized solution")
        plt.legend()

        #geo plot
        plotGeo(ids=closest_row[2],ax=ax_geo,reload=True)


        fig.canvas.draw()


    fig.canvas.mpl_connect('scroll_event', on_scroll)
    fig.canvas.mpl_connect('button_press_event', on_click)


def plotBoth():
    fig, (ax_geo,ax_scatter) = plt.subplots(1, 2, figsize=(10, 5))

    ax_scatter.set_title('Pareto frontier')
    plotInteractive(fig, ax_scatter, ax_geo)

    ax_geo.set_title('Geodata')
    plotGeo(ax=ax_geo)
    
    plt.tight_layout()
    plt.show()



if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    plotBoth()
