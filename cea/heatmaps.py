"""
===========================
Heatmapping algorithm
===========================
J. Fonseca  script development          27.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox

"""
from __future__ import division
import pandas as pd
import os
import arcpy
import tempfile


class HeatmapsTool(object):

    def __init__(self):
        self.label = 'Heatmaps'
        self.description = 'Create heatmap data layers'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_data = arcpy.Parameter(
            displayName="File containing the data to read (Total_demand.csv)",
            name="path_data",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_data.filter.list = ['csv']
        analysis_field_variables = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_field_variables",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_field_variables.filter.list = []
        path_buildings = arcpy.Parameter(
            displayName="Buildings file",
            name="path_buildings",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_buildings.filter.list = ['shp']
        path_results = arcpy.Parameter(
            displayName="Results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        return [path_data, analysis_field_variables,
                path_buildings, path_results]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        path_data = parameters[0]
        analysis_field_variables = parameters[1]
        csv = pd.read_csv(path_data.valueAsText)
        fields = set(csv.columns.tolist())
        fields.remove('Name')
        analysis_field_variables.filter.list = list(fields)
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        path_data = parameters[0].valueAsText
        value_table = parameters[1].value
        path_buildings = parameters[2].valueAsText
        path_results = parameters[3].valueAsText
        path_variables = os.path.dirname(path_data)
        path_temporary_folder = tempfile.gettempdir()
        file_variable = os.path.basename(path_data)
        analysis_field_variables = [value_table.getvalue(i, 0)
                                    for i in range(value_table.rowcount)]
        heatmaps(
            analysis_field_variables=analysis_field_variables,
            path_variables=path_variables,
            path_buildings=path_buildings,
            path_results=path_results,
            path_temporary_folder=path_temporary_folder,
            file_variable=file_variable)


def heatmaps(
        analysis_field_variables,
        path_variables,
        path_buildings,
        path_results,
        path_temporary_folder,
        file_variable):
    """
    algorithm to calculate heat maps out of n variables of interest

    Parameters
    ----------
    path_variables:
        path to folder with variables to be mapped: the options:
            - .../../../demand
            - .../../../emissions
    file_variable:
        file name in folder to do the calculation
            - Total_demand.csv
            - cooling_LCA.csv
            - ../../../emissions/heating_LCA.csv
            - ../../../emissions/electricity_LCA.csv
            - ../../../emissions/Total_LCA_embodied.csv
            - ../../../emissions/Total_LCA_operation.csv.
    analysis_field_variables: array
        when the path variables is selected, an array of n variables 'string'
        will be elaborated based on the selection of n input fields. For this a
        form like the one used in the Arcgis function "merge/FieldMap could
        be used.
    path_buildings : string
        path to buildings file buildings.shp
    path_temporary_folder : string
        folder to store temporal files
    path_results : string
        path to store results: folder heatmaps

    Returns
    -------
    heat map of variable n: .tif
        heat map file per variable of interest n.
    """

    # local variables
    vector = [[]]
    arcpy.env.overwriteOutput = True
    arcpy.FeatureToPoint_management(
        path_buildings,
        path_temporary_folder +
        '\\' +
        'temp1.shp',
        "CENTROID")
    arcpy.MakeFeatureLayer_management(
        path_temporary_folder +
        '\\' +
        'temp1.shp',
        "lyr",
        "#",
        "#")
    for field in analysis_field_variables:
        arcpy.AddField_management(
            "lyr",
            field,
            "DOUBLE",
            "#",
            "#",
            "#",
            "#",
            "NULLABLE",
            "NON_REQUIRED",
            "#")
        vector.append([])
    arcpy.AddJoin_management(
        "lyr",
        "Name",
        os.path.join(path_variables, file_variable),
        "Name",
        "KEEP_ALL")
    arcpy.CheckOutExtension("Spatial")
    # Null values to Zero:.

    def RemoveNULL(x):
        if x is None:
            return 0
        elif x == '':
            return 0
        else:
            return x

    fields = [file_variable+"."+a for a in analysis_field_variables]
    with arcpy.da.SearchCursor("lyr", fields) as cursor:
        for row in cursor:
            for n in range(len(fields)):
                vector[n].append(RemoveNULL(row[n]))
    counter = 0
    with arcpy.da.UpdateCursor(os.path.join(path_temporary_folder, 'temp1.shp'), analysis_field_variables) as cursor:  # noqa
        for row in cursor:
            for n in range(len(fields)):
                row[n] = vector[n][counter]
                cursor.updateRow(row)
            counter += 1

    for field in analysis_field_variables:
        arcpy.gp.Idw_sa(
            os.path.join(path_temporary_folder, 'temp1.shp'),
            field,
            os.path.join(path_results, field),
            "1", "2", "VARIABLE 12")

    arcpy.Delete_management("in_memory/building_points")


def test_heatmaps():
    analysis_field_variables = ["Qhsf", "Qcsf"]  # noqa
    path_buildings = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\101_input files\feature classes'+'\\'+'buildings.shp'  # noqa
    path_variables = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\103_final output\demand'  # noqa
    path_results = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\103_final output\heatmaps'  # noqa
    path_temporary_folder = tempfile.gettempdir()
    file_variable = 'Total_demand.csv'
    heatmaps(
        analysis_field_variables,
        path_variables,
        path_buildings,
        path_results,
        path_temporary_folder,
        file_variable)

if __name__ == '__main__':
    test_heatmaps()