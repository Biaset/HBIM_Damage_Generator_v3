import pandas as pd
import ifcopenshell.guid as guid
import ifcopenshell.api as api
from ifcopenshell.guid import new as new_guid
import bpy
from datetime import datetime

def pset_epoch_id(date_str):
    dt = datetime.strptime(date_str, '%d-%m-%Y %H:%M')
    epoch_id = dt.strftime('%d%m%Y')
    pset = f'PTUM_BiologicalColonization_{epoch_id}'
    return pset

class IfcQuery:
    def __init__(self, guid, model):
        self.guid = guid
        self.model = model

    def find_element_by_guid(self):
        return self.model.by_guid(self.guid)

    def guid_to_ifc_type(self):
        if pd.isna(self.guid):
            return None
        elem = self.model.by_guid(str(self.guid))
        return elem.is_a() if elem else None
    
    # def get_blender_object_from_guid(guid):
    #     for obj in bpy.data.objects:
    #         if obj.type != "MESH":
    #             continue
    #         if obj.get("IfcGlobalId") == guid:
    #             return obj
    #         if obj.get("GlobalId") == guid:
    #             return obj
    #     return None

    def get_blender_object_from_ifc_guid(self):
        host_ifc = self.model.by_guid(self.guid)
        if host_ifc is None:
            return None

        step_id = host_ifc.id()

        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            if hasattr(obj, "BIMObjectProperties"):
                if obj.BIMObjectProperties.ifc_definition_id == step_id:
                    return obj
        return None
  

class DamageCreation:
    def __init__(self, model):
        #self.element = element
        self.model = model
        #self.pset_name = pset_name
        # self.covering = None
        # self.proxy = None
        #self.storey = self.element.ContainedInStructure[0].RelatingStructure
        self.storey = None
        self.product = None

    def get_or_create_damage(self, guid_value, element, damage_name, damage_type):

        for obj in self.model.by_type('IfcProduct'):
            if obj.GlobalId == guid_value:
                return obj

        if damage_type in ['Lichen', 'Moss', 'Bacteria']:

            self.product = api.run(
                'root.create_entity',
                self.model,
                ifc_class='IfcCovering',
                name=damage_name
            )

            self.product.PredefinedType = 'USERDEFINED'
            storey = element.ContainedInStructure[0].RelatingStructure

            rel = api.run(
                'root.create_entity',
                self.model,
                ifc_class="IfcRelCoversBldgElements"
            )
            rel.RelatingBuildingElement = element
            rel.RelatedCoverings = [self.product]

            api.run(
                'spatial.assign_container',
                self.model,
                products=[self.product],
                relating_structure=storey
            )

        else:
            self.product = api.run(
                'root.create_entity',
                self.model,
                ifc_class='IfcBuildingElementProxy',
                name=damage_name
            )

            self.product.PredefinedType = 'USERDEFINED'
            storey = element.ContainedInStructure[0].RelatingStructure

            rel = api.run(
                'root.create_entity',
                self.model,
                ifc_class="IfcRelAssignsToProduct"
            )
            rel.RelatingProduct = element
            rel.RelatedObjects = [self.product]

            api.run(
                'spatial.assign_container',
                self.model,
                products=[self.product],
                relating_structure=storey
            )
        return self.product

    def attach_epoch_pset(self, properties, pset_name):

        pset = api.run(
            'pset.add_pset',
            self.model,
            product=self.product,
            name=pset_name
        )

        api.run(
            'pset.edit_pset',
            self.model,
            pset=pset,
            properties=properties
        )
        return pset  

    def ingest_multiple_damage_csv(self, csv, pset_name, observation_time):
        
        for _, row in csv.iterrows():
            if row['timestamp'] == observation_time:
                element = IfcQuery(row['host_id'], self.model).find_element_by_guid()
                damage = row['damage_type']
                damage_guid = row['damage_id']
                damage_name = f'BiologicalColonization_{str(damage).title()}'
                # prop = {
                #     'DecayType': damage,
                #     # 'CoverageRatio': row['Coverage'],
                #     # 'SeverityLevel': row['Severity'],
                #     'ObservationDate': row['timestamp']
                # }
                prop = {
                    'DecayType_PTUM': damage,
                    'ObservationDate_PTUM': row['timestamp'],
                    'SurveyMethod_PTUM': 'Laser Scanner',
                    'DeviceModel_PTUM': 'Leica BLK360',
                    'SurfaceLocation_PTUM': 'External',
                    'SeverityLevel_PTUM': 'MEDIUM',
                    'CoverageArea_PTUM': '0.23 m2'
                }
                # if damage == 'plant':
                #     self.create_new_proxy_damage(element, damage_name)
                #     self.psets_for_proxy_damage(prop, pset_name)
                # else:
                #     self.create_new_covering_damage(element, damage_name)
                #     self.pset_for_covering_damage(prop, pset_name)
                self.get_or_create_damage(damage_guid, element, damage_name, damage)
                self.attach_epoch_pset(prop, pset_name)  