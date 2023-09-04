import json                     # For loading and writing json files
import os                       # For getting the user's name
import tkinter                  # For generating a file selector window
import tkinter.filedialog
import requests                 # For loading the json schema from the web
from datetime import datetime   # For determining the creation time
import panel as pn              # for displaying the JSON Editor
pn.extension()

class MetaDataCreator:
    """ Panel application to generate and modify json files based on the NERDm
        schema of NIST. See https://data.nist.gov/od/dm/nerdm/ for more details.
        Methods:
            set_schema(proxy: dict=None): Loads the json schema from the web and
                                          sets the attributes.
            init_layout(): Initialized the panel.Layout to show.
            show_layout(): Shows the layout by opening a browser.
            save_file(event: Any=None): Saves the json file to disk. 
            load_file(event: Any=None): Loads a json file from disk.
            create_obj(event: Any=None): Creates a json object and
                                         shows it in an editor.
            add_obj(event: Any=None): Appends a json object to the output json.
    """
    def __init__(self, proxy=None):
        """
        Args:
            proxy (dict, optional): If proxies are needed to access the web, set
                                proxy={"http": "proxy_http_url:proxy_port",
                                       "https": "proxy_https_url:proxy_port"}

        """

        # Link to the used schema
        self.schema_url = "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3"

        # Define header information 
        self.creation_time = datetime.now()
        time_str = f"{self.creation_time.year}-{self.creation_time.month}-{self.creation_time.day} " \
                   + f"{self.creation_time.hour}:{self.creation_time.minute}"
        self.creator = os.getlogin()
        self.data = {"$schema": self.schema_url, "Created on": time_str,
                     "Author": self.creator, "Licence": "CC-BY",
                     "Licence URL": "https://creativecommons.org/licenses/by/4.0/legalcode"}
        
        self._spacer = pn.Spacer(width=520)
        self._editor_width = 500
        self._button_width = 100
        
        self.set_schema(proxy=proxy)
        self.init_layout()
        self.show_layout()

    def show_layout(self):
        self.layout.show()
        
    def set_schema(self, proxy=None):
        """ Sets the schema attributes by loading the json schema from the web.
            If a proxy need to be used to access the web, it can be given as
            an argument.
        Args:
            proxy (dict, optional): If proxies are needed to access the web, set
                                proxy={"http": "proxy_http_url:proxy_port",
                                       "https": "proxy_https_url:proxy_port"}

        """
        
        # Initialize the web session
        session = requests.Session()
        if proxy is not None:
            session.proxies.update(proxy)

        # Actually two schemas are used. In order to get the auto-correction to
        # work properly, the schmas are mixed. For this, some reference paths 
        # has to be replaced. 
        replace_path = "https://data.nist.gov/od/dm/nerdm-schema/v0.3"

        # Set the url to the two schemas.
        schema_path = "https://data.nist.gov/od/dm/nerdm-schema/" \
                      + "nerdm-schema-0.3.json"
        ext_schema_path = "https://data.nist.gov/od/dm/nerdm-schema/pub/" \
                          + "nerdm-pub-schema-0.3.json"
        
        # Load the extension schema and replace the reference paths
        ext_schema_json = session.get(ext_schema_path, allow_redirects=False)
        ext_schema = json.loads(
            ext_schema_json.text.strip().replace(replace_path, ""))

        # Load the core schema
        schema_json = session.get(schema_path, allow_redirects=False)
        self.schema = json.loads(schema_json.text.strip())

        # Include the extension objects in the core schema
        for key, val in ext_schema["definitions"].items():
            self.schema["definitions"][key] = val

        # Change the schema a bit, such that multiple objects of the same type
        # can be created by keeping the auto-correction feature.
        # For this a 'MetaData' object will be defined, which has array
        # properties for each object defined in the NERDm schema.
        self.out_schema = {}
        self.out_schema["title"] = "MetaData"
        self.out_schema["MetaData"] = {"properties": {"title": "Meta Data"}}
        self.out_schema["definitions"] = {}

        prop_link = self.out_schema["MetaData"]["properties"]
        for key, val in self.schema["definitions"].items():
            prop_link[key+" list"] = {
                "description": f"List of {key} objects", "type": "array",
                "items": {"$ref": f"#/definitions/{key}"}}
            self.out_schema["definitions"][key] = val
        
        self.out_schema["$ref"] = "#/MetaData"

    def init_layout(self):
        """ Initialized the panel.Layout object.
        """
        # To easily see all accessible objects including properties, etc.,
        # an editor will be created, which shows these objects.
        # First the objects for the 'schema view' will be sorted by their names.
        s_v_out = dict(sorted(self.schema["definitions"].items()))

        # Set the name, which should be shown for this view and define the
        # JSONEditor
        s_v_s = {"title": "Schema"}
        self.schema_view = pn.widgets.JSONEditor(
            value=s_v_out, width=self._editor_width, mode="view", schema=s_v_s)
        
        # One should be able to select and generate single objects.
        # All names of the objects will be gathered.
        self.schema_name = []

        for name in self.schema["definitions"]:
            self.schema_name.append(name)
        self.schema_name.sort()

        # Define the object selector
        self.object_select = pn.widgets.Select(
            options=self.schema_name, width=200)
        
        # Define some buttons for different tasks
        self.create_button = pn.widgets.Button(
            name="Create", width=self._button_width)
        self.add_button = pn.widgets.Button(
            name="Add", width=self._button_width)
        self.save_button = pn.widgets.Button(
            name="Save", width=self._button_width)
        self.load_button = pn.widgets.Button(
            name="Load", width=self._button_width)

        # Define the actually Editor for the json file to be generated/edited.
        self.json_editor = pn.widgets.JSONEditor(
            value=self.data, schema=self.out_schema, width=self._editor_width,
            mode="tree")

        # Define the layout
        self.layout = pn.Column(
            pn.Row(pn.Spacer(width=200), self.save_button, self.load_button,
                   pn.Spacer(width=200), self.object_select,
                   self.create_button, self.add_button),
            pn.Row(self.json_editor,
                   pn.Column(self._spacer, self._spacer,  self._spacer),
                   self.schema_view))
        
        # Apply functions to the buttons
        self.create_button.on_click(self.create_obj)
        self.add_button.on_click(self.add_obj)
        self.save_button.on_click(self.save_file)
        self.load_button.on_click(self.load_file)   
        
    def save_file(self, event=None):
        """ Open a window to select a file/file path to save the json file.
            Args:
                event (Any, optional): Needed for assigning to panel.Buttons.
        """

        # Create a window, in which a file or file path can be selected
        root = tkinter.Tk()
        root.withdraw()                                        
        root.call('wm', 'attributes', '.', '-topmost', True)   
        path = tkinter.filedialog.asksaveasfilename(
            filetypes=[("JSON Files", "*.json")],
            defaultextension=[("JSON Files", "*.json")])
        root.destroy()

        # Check if a file/path is selected or if the window is closed before.
        if path != "":
            # Save the data as a json file
            with open(path, "w") as f:
                f.write(json.dumps(self.layout[1][0].value, indent=4))

    def load_file(self, event=None):
        """ Open a window to select a json file to load.
            Args:
                event (Any, optional): Needed for assigning to panel.Buttons.
        """

        # Create a window, in which a file can be selected.
        root = tkinter.Tk()
        root.withdraw()                                        
        root.call('wm', 'attributes', '.', '-topmost', True)   
        path = tkinter.filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")])
        root.destroy()

        # Check if a file is selected or if the window is closed before.
        if path != "":
            # Load the data from the json file
            with open(path, "r") as f:
                self.layout[1][0] =  pn.widgets.JSONEditor(
                    value=json.load(f), schema=self.out_schema,
                    width=self._editor_width)
            # Set the rest of the layout to the initial state
            self.layout[1][1] = pn.Column(self._spacer, self._spacer, self._spacer)

    def _translate_type(self, t:str):
        if t == "array":
            return []
        elif t == "string":
            return ""
        return dict()

    def _get_type(self, schema:dict):
        """ Determines the type of a schema/json object and returns the python
            equivalent initial object. 
            
            Args:
                schema (dict): A json object translated to a dictionary.

            Returns:
                '' in case of type(schema) = 'string',
                list() in case of type(schema) = 'array',
                else dict()
        """

        # Initialize the output
        v = dict()
        # If schema has a 'properties' key, it is an object.
        if not "properties" in schema:
            if "type" in schema:
                v = self._translate_type(schema["type"])

            # Find the first non 'null' type.
            elif "anyOf" in schema:
                for dic in schema["anyOf"]:
                    if "type" in dic:
                        if dic["type"] == "null":
                            continue
                        v = self._translate_type(dic["type"])
                        break

            # The object inherits from another object. 
            elif "$ref" in schema:
                return self._get_type(
                    self.schema["definitions"][schema["$ref"].split("/")[-1]])
        return v
    
    def _get_ndrm_type(self, name:str, schema:dict):
        """ Determines the name of schema/json and all names of objects
            it inherit from. 
            
            Args:
                schema (dict): A json object translated to a dictionary.
            
            Returns:
                list of strings
        """

        # Initialize the output
        v = [f"ndrm:{name}"]

        # The object inherits from at least one object.
        if "allOf" in schema:
            for dic in schema["allOf"]:
                if "$ref" in dic:
                    new_name = dic["$ref"].split("/")[-1]
                    for n in self._get_ndrm_type(new_name,
                            self.schema["definitions"][new_name]):
                        v.append(n)

        # The object inherits from one object.
        elif "$ref" in schema:
            new_name = schema["$ref"].split("/")[-1]
            for n in self._get_ndrm_type(new_name,
                    self.schema["definitions"][new_name]):
                v.append(n)
        return v
    
    def _get_prop_type(self, name:str, schema:dict):
        """ Determines the type of a schema/json object's property and returns
            the python quivalent initial object. 
            
            Args:
                name (str): The name of the property.
                schema (dict): A json object translated to a dictionary to
                               which the property belongs.

            Returns:
                '' in case of type(property) = 'string',
                list() in case of type(property) = 'array',
                else dict()
        """

        # If the object (schema) has no field 'properties' or, if the property
        # is not included in 'properties', a empty string is returned. 
        try:
            prop = schema["properties"][name]
        except KeyError:
            return ""

        if "type" in prop:
            return self._translate_type(prop["type"])
        
        # The property inherits from another object
        elif "$ref" in prop:
            mother = prop["$ref"].split("/")[-1]
            return self._get_type(self.schema["definitions"][mother])
        # 'allOf' means that the property is of type 'object'.
        elif "allOf" in prop:
            return dict()
        
        # Find the first non 'null' type
        elif "anyOf" in prop:
            for dic in prop["anyOf"]:
                if "type" in dic:
                    if dic["type"] == "null":
                        continue
                    return self._translate_type(dic["type"])
            for dic in prop["anyOf"]:
                if "$ref" in dic:
                    mother = prop["$ref"].split("/")[-1]
                    return self._get_type(self.schema["definitions"][mother])
                
    def _get_properties(self, schema:dict):
        """ Get all properties, required properties and types of required
            properties of a json object.

            Args:
                schema (dict): A json object translated to a dictionary.
            
            Returns:
                properties (dict), required properties (list of strings),
                required types (list of empty dictionaries, strings and lists)
                """
        if type(self._get_type(schema)) == dict:
            # Initialize the output
            required = []
            required_types = []

            # No recursion is needed
            if "properties" in schema:
                if "required" in schema:
                    required = schema["required"].copy()
                    for req in required:
                        required_types.append(
                            self._get_prop_type(req, schema))
    
                return schema["properties"].copy(), required, required_types
            
            # The object inherits from another one
            elif "$ref" in schema:
                return self._get_properties(
                    self.schema["definitions"][schema["$ref"].split("/")[-1]])
            
            # Get all (required) properties of all objects the current object
            # inherits from.
            elif "allOf" in schema:
                out_props = {}
                for dic in schema["allOf"]:
                    if "properties" in dic:
                        for prop in dic["properties"]:
                            if not prop in out_props:
                                out_props[prop] = dic["properties"][prop]
                    if "required" in dic:
                        for prop in dic["required"]:
                            if not prop in required:
                                required.append(prop)
                                required_types.append(
                                    self._get_prop_type(prop, dic))
                    elif "$ref" in dic:
                        tmp_props, tmp_req, tmp_req_types = \
                                self._get_properties(self.schema[
                                    "definitions"][dic["$ref"].split("/")[-1]])
                        for prop in tmp_props:
                            if not prop in out_props:
                                out_props[prop] = tmp_props[prop]
                        for i, prop in enumerate(tmp_req):
                            if not prop in required:
                                required.append(prop)
                                required_types.append(tmp_req_types[i])

                return out_props, required, required_types
        else:
            # The object is of type string or array and thus has no properties.
            return dict(), list(), list()

    def create_obj(self, event=None):
        """ Creates a given json object by setting all required fields and
            displays it in a panel.JSONEditor. Also a list of all possible
            properties will be shown in a separate editor.

            Args:
                event (Any, optional): Needed for assigning to panel.Buttons.
        """

        # Get the schema and type of the object, which will be generated.
        s = self.schema["definitions"][self.object_select.value].copy()
        v = self._get_type(s)

        if type(v) == dict:
            # Get all possible properties and required properties.
            this_props, this_req, this_types = self._get_properties(s)

            # Initialize the @type and @id fields, if existing for this object. 
            if "@type" in this_props:
                v["@type"] = self._get_ndrm_type(self.object_select.value, s)
            if "@id" in this_props:
                v["@id"] = ""

            # Initialize all required properties.
            for i, req in enumerate(this_req):
                v[req] = this_types[i]

            # Show object's notes in a separate editor, if they exist.
            if "notes" in self.schema["definitions"][self.object_select.value]:
                notes_dict = self.schema["definitions"][
                    self.object_select.value]["notes"].copy()
                self.layout[1][1][2] =  pn.widgets.JSONEditor(
                    value=notes_dict, mode="view", width=self._editor_width,
                        menu=False, schema={"title": "Notes"})
            else:
                self.layout[1][1][2] = pn.Spacer(width=520)

            self.layout[1][1][1] = pn.widgets.JSONEditor(
                value=this_props, width=self._editor_width, mode="view",
                schema={"title": self.object_select.value + " Properties"})
        else:
            # There are no properties to show, because the object is of type
            # string or array.
            self.layout[1][1][1] = pn.Spacer(width=520)

        s["definitions"] = self.schema["definitions"]
        s["title"] = self.object_select.value
        self.layout[1][1][0] = pn.widgets.JSONEditor(
                value=v, schema=s, width=self._editor_width, mode="tree",
                search=False)

    def add_obj(self, event=None):
        """ Add the json object shown in the object's editor to the
            actually meta data json. 

            Args:
                event (Any, optional): Needed for assigning to panel.Buttons.
        """

        try:
            # If the object's editor does not exist, an AttributeError
            # will be raised.
            tmp_data = self.layout[1][0].value
            key = f"{self.object_select.value} list"

            # Checks if any objects of the same type already exist.
            if key in tmp_data:
                tmp_data[key].append(self.layout[1][1][0].value)
            else:
                tmp_data[key] = [self.layout[1][1][0].value]
    
            # Update the view.
            self.layout[1][0] =  pn.widgets.JSONEditor(
                value=tmp_data, schema=self.out_schema,
                width=self._editor_width)
        except AttributeError:
            pass

# proxy = {"http": "http://some_url:some_port",
#         "https": "http://some_url:some_port"}

# meta_json = MetaDataCreator(proxy=proxy)
meta_json = MetaDataCreator()