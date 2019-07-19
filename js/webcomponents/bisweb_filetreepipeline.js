const bis_webutil = require('bis_webutil.js');
const bis_webfileutil = require('bis_webfileutil.js');

const moduleIndex = require('moduleindex.js');
const bisweb_custommodule = require('bisweb_custommodule.js');

const bis_genericio = require('bis_genericio.js');
const bootbox = require('bootbox');
const $ = require('jquery');

//TODO: When Xenios gets back have him update biswebnode
class FileTreePipeline extends HTMLElement {
    
    constructor() {
        super();
        this.panel = null;
        this.pipelineModal = null;
        this.modules = [];
        this.savedParameters = null;
        this.pipelineInputs = null;
    }

    connectedCallback() {
        let algocontrollerid = this.getAttribute('bis-algocontrollerid');
        bis_webutil.runAfterAllLoaded( () => {     
            this.algocontroller = document.querySelector(algocontrollerid);
        });
    }
    
    /**
     * Creates the collapsible HTML element inside a parent object, most typically the left sidebar.
     *  
     * @param {HTMLElement|JQueryElement} parent - The parent element in which to render the menu.
     */
    createPanel(parent) {
        let body = bis_webutil.createCollapseElement(parent, 'Study Tools', false);

        let panelBody = $(`
            <div>
                <div id='bisweb-panel-tasks'>
                    <label>Tasks</label><br>
                </div>
                <div id='bisweb-panel-pipeline'>
                    <label>Pipeline Tools</label><br>
                </div> 
            </div>
        `);

       
        body.append(panelBody);

        let taskButtonBar = this.createTaskElements();
        panelBody.find('#bisweb-panel-tasks').append(taskButtonBar);

        let pipelineButtonBar = this.createPipelineElements();
        panelBody.find('#bisweb-panel-pipeline').append(pipelineButtonBar);
        console.log('panel body', panelBody.find('#bisweb-panel-pipeline'));
        
    }

    /**
     * Create the set of buttons used to manage loading and clearing task files. 
     */
    createTaskElements() {

        let taskButtonBar = bis_webutil.createbuttonbar();

        let importTaskButton = bis_webfileutil.createFileButton({
            'type': 'info',
            'name': 'Import task file',
            'callback': (f) => {
                this.graphelement.chartInvokedFrom = 'task';
                this.loadStudyTaskData(f);
            },
        },
            {
                'title': 'Import task file',
                'filters': [
                    { 'name': 'Task Files', extensions: ['json'] }
                ],
                'suffix': 'json',
                'save': false,
            });

        let clearTaskButton = bis_webutil.createbutton({ 'name': 'Clear tasks', 'type': 'primary' });
        clearTaskButton.on('click', () => {
            bootbox.confirm({
                'message': 'Clear loaded task data?',
                'buttons': {
                    'confirm': {
                        'label': 'Yes',
                        'className': 'btn-success'
                    },
                    'cancel': {
                        'label': 'No',
                        'className': 'btn-danger'
                    }
                },
                'callback': (result) => {
                    if (result) { this.graphelement.taskdata = null; }
                }
            });
            this.graphelement.taskdata = null;
        });

        let plotTasksButton = bis_webutil.createbutton({ 'name': 'Plot task charts', 'type': 'info' });
        plotTasksButton.on('click', () => {
            this.graphelement.chartInvokedFrom = 'task';
            this.filetree.parseTaskImagesFromTree();
        });

        let drawingInterfaceButton = bis_webutil.createbutton({ 'name' : 'Open drawing interface', 'type' : 'primary' });
        drawingInterfaceButton.on('click', () => {
            this.startDrawingInterface();
        });
        
        plotTasksButton.addClass('bisweb-load-enable');
        plotTasksButton.prop('disabled', 'true');

        taskButtonBar.append(importTaskButton);
        taskButtonBar.append(clearTaskButton);
        taskButtonBar.append(plotTasksButton);
        taskButtonBar.append(drawingInterfaceButton);

        return taskButtonBar;
    }

    createPipelineElements() {
        let pipelineButtonBar = bis_webutil.createbuttonbar();

        let pipelineCreationButton = bis_webutil.createbutton({ 'name' : 'Create pipeline', 'type' : 'info'});
        pipelineCreationButton.on('click', () => {
            this.openPipelineCreationModal();
        });

        let pipelineBody = $(`<div></div>`);
        let pipelineTable = $(`
            <ul class='list-group bisweb-pipeline-list'>
            </ul>
        `);

        pipelineButtonBar.append(pipelineCreationButton);
        pipelineBody.append(pipelineButtonBar);
        pipelineBody.append(pipelineTable);

        return pipelineBody;
    }

    /**
     * Opens a modal that will allow a user to create a pipeline from the full set of BioImageSuite Web Modules. Should be called by outside scope!
     */
    openPipelineCreationModal() {
        if (!this.pipelineModal) {

            let pipelineModal = bis_webutil.createmodal('Create a pipeline', 'modal-lg');
            pipelineModal.footer.empty();

            let addModuleButton = bis_webutil.createbutton({ 'name' : 'Add module', 'type' : 'success' });

            addModuleButton.on('click', () => {
                let moduleIndexKeys = moduleIndex.getModuleNames();
                let moduleIndexArray = [];
                
                for (let key of moduleIndexKeys) {
                    moduleIndexArray.push({ 'text' : moduleIndex.getModule(key).getDescription().name, 'value' : key });
                }

                bootbox.prompt({
                    'size' : 'small', 
                    'title' : 'Choose a module',
                    'inputType' : 'select',
                    'inputOptions' : moduleIndexArray,
                    'callback' : (moduleName) => {
                        if (moduleName) {
                            let mod = moduleIndex.getModule(moduleName);

                            let width = pipelineModal.body.width() / 3;
                            let customModule = bisweb_custommodule.createCustom(null, this.algocontroller, mod, { 'numViewers': 0, 'dual' : false, 'paramsMargin' : '5px', 'buttonsMargin' : '0px', 'width' : width });
                            customModule.createOrUpdateGUI({ 'width' : width });
                            centerCustomElement($(customModule.panel.widget));

                            let id = bis_webutil.getuniqueid();
                            this.modules.push({ 'name' : moduleName, 'module' : customModule, 'id' : id});

                            let moduleLocation = this.modules.length - 1; //index of module in array at time of adding
                            let prettyModuleName = moduleIndex.getModule(moduleName).getDescription().name;

                            //add 'remove' button to modal button bar
                            let removeButton = bis_webutil.createbutton({ 'name': 'Remove', 'type' : 'danger' });
                            removeButton.on('click', () => {
                                bootbox.confirm({
                                    'message' : `Remove module ${prettyModuleName}?`,
                                    'size' : 'small',
                                    'callback' : (result) => {
                                        if (result) {
                                            this.modules.splice(moduleLocation, 1);
                                            pipelineModal.body.find(`#${id}`).remove();
                                        }
                                    }
                                });
                            });

                            //put label and element inside a containing div
                            let moduleLabel = $(`<span>${prettyModuleName}</span>`);

                            $(customModule.panel.widget).find('.bisweb-customelement-footer').append(removeButton);
                            $(customModule.panel.widget).prepend(moduleLabel);
                            $(customModule.panel.widget).attr('id', id);
                            
                            this.addArrowButtons(id, this.pipelineModal, $(customModule.panel.widget).find('.dg.main') );
                            pipelineModal.body.append(customModule.panel.widget);
                        }
                    }
                });
            });

            let saveModulesButton = bis_webfileutil.createFileButton({ 
                'name': 'Save Modules',
                'type': 'primary',
                'callback': (f) => { this.savePipelineToDisk(f); pipelineModal.dialog.modal('hide'); },
                }, {
                    'title': 'Save Pipeline to Disk',
                    'save': true,
                    'filters': [{ name: 'JSON Files', extensions: ['json'] }],
                    'suffix': 'json',
                    'initialCallback': () => {
                        return 'pipeline.json';
                    }
            });

            let importInputsButton = bis_webfileutil.createFileButton({
                'name': 'Import Inputs',
                'type': 'info',
                'callback': (f) => { this.importInputsFromDisk(f); },
                }, {
                    'title': 'Import inputs from disk',
                    'save': false,
                    'filters': 'NII',
                    'suffix': 'NII',
                    'altkeys' : true
            });

            //set pipeline modal to update its modules when it's hidden and shown, so long as no settings are saved so far.
            pipelineModal.dialog.on('show.bs.modal', () => {
                if (!this.savedParameters) {
                    for (let obj of this.modules) {
                        obj.module.createOrUpdateGUI();
                    }
                }
            });

            pipelineModal.footer.append(addModuleButton);
            pipelineModal.footer.append(saveModulesButton);
            pipelineModal.footer.append(importInputsButton);
            this.pipelineModal = pipelineModal;
        }

        this.pipelineModal.dialog.modal('show');
    }

    /**
     * Adds arrow buttons that will allow a user to move a module up or down in the pipeline. 
     * 
     * @param {String} id - Id associated with a module currently in the pipeline modal.
     * @param {JQuery} modal - The pipeline modal.
     * @param {JQuery} moduleContainer - The div containing the module to move up or down.
     */
    addArrowButtons(id, modal, moduleContainer) {
        let upButton = $(`<span class='glyphicon glyphicon-chevron-up bisweb-glyphicon-right'></span>`);
        let downButton = $(`<span class='glyphicon glyphicon-chevron-down bisweb-glyphicon-right'></span`);

        upButton.on('click', () => {
            let prevElem, currentElem; 
            for (let i = 0; i < this.modules.length; i++) {
                if (this.modules[i].id === id) { 
                    if (i === 0) { return; } //can't move up if this is the first item in the list
                    prevElem = $(modal.body).find('#' + this.modules[i - 1].id);
                    currentElem = $(modal.body).find('#' + this.modules[i].id);

                    //move module up one in list
                    let moveElem = this.modules.splice(i, 1);
                    this.modules.splice(i - 1, 0, moveElem[0]);
                }
            }

            $(currentElem).detach();
            $(currentElem).insertBefore(prevElem);
        });

        downButton.on('click', () => {
            let nextElem, currentElem; 
            for (let i = 0; i < this.modules.length; i++) {
                if (this.modules[i].id === id) { 
                    if (i === this.modules.length - 1) { return; } //can't move down if this is the last item in the list
                    nextElem = $(modal.body).find('#' + this.modules[i + 1].id);
                    currentElem = $(modal.body).find('#' + this.modules[i].id);

                    //move module down one in list
                    let moveElem = this.modules.splice(i, 1);
                    this.modules.splice(i + 1, 0, moveElem[0]);
                    i = this.modules.length; //needed to avoid double-counting the element after it's moved into place.
                }
            }

            $(currentElem).detach();
            $(currentElem).insertAfter(nextElem);
        });

        $(moduleContainer).prepend(upButton);
        $(moduleContainer).append(downButton);
    }

    /**
     * Saves the modules to disk, in order, with the parameters the user specified.
     * Also runs the pipeline module and saves a Makefile for the modules specified and an output directory for the files that will be created by it.
     * 
     * @param {String} filename - Name for the pipeline parameters file. 
     */
    savePipelineToDisk(filename) {
        let params = [];
        $('.bisweb-pipeline-list').empty();
        for (let i = 0; i < this.modules.length; i++) {
            let param = {'name' : this.modules[i].name, 'params' : this.modules[i].module.getVars()};
            params.push(param);

            //update pipeline list 
            let moduleName = moduleIndex.getModule(this.modules[i].name).getDescription().name;
            let listItem = this.createPipelineListItem(moduleName);
            $('.bisweb-pipeline-list').append(listItem);
        }

        this.savedParameters = params;
        
        //format the saved modules to use the pipeline creation tool.
        //TODO: Format this to use biswebnode maybe? 
        let command = ['', 'home', 'zach', 'javascript', 'bisweb', 'js', 'bin', 'bisweb.js'].join('/');
        let pipeline = { 
            'command' : 'node ' + command,
            'inputs' : [{
                'name' : 'input',
                'files' : [
                    '/home/zach/javascript/bisweb/test/testdata/MNI_2mm_orig.nii.gz',
                    '/home/zach/javascript/bisweb/test/testdata/MNI_2mm_resliced.nii.gz',
                    '/home/zach/javascript/bisweb/test/testdata/MNI_2mm_scaled.nii.gz'
                ]
            }],
            'jobs' : []
        };
        for (let i = 0; i < params.length; i++) {
            let inputName = (i === 0 ? 'input' : 'out' + i), outputName = 'out' + (i + 1);
            let entry = {
                'name' : `Command ${i}`,
                'subcommand' : params[i].name,
                'options' : `--input %${inputName}% --output %${outputName}% `,
                'outputs' : [
                    {
                        'name' : outputName,
                        'depends' : [ `%${inputName}%`],
                        'naming' : `${params[i].name}_%${inputName}%.nii.gz`
                    }
                ]
            };

            for (let p of Object.keys(params[i].params)) {
                entry.options = entry.options.concat(`--${p} ${params[i].params[p]} `);
            }

            pipeline.jobs.push(entry);
        }

        let stringifiedPipeline = JSON.stringify(pipeline, null, 2);
        bis_genericio.write(filename, stringifiedPipeline).then( () => {

            //construct default output directory and Makefile names from the user-provided filename
            //splitByPathSeparator used for platform agnosticity
            let splitOutputFilename = splitByPathSeparator(filename), splitOdirFilename = splitByPathSeparator(filename);
            splitOutputFilename.name[splitOutputFilename.name.length - 1] = 'Makefile', splitOdirFilename.name[splitOdirFilename.name.length - 1] = 'FilesCreatedByPipeline';

            let outputFilename = splitOutputFilename.name.join(splitOutputFilename.sep);
            let odirFilename = splitOdirFilename.name.join(splitOdirFilename.sep);

            //savemanually flag needed in order to save the output Makefile (modules run directly through the server don't hit the saving hooks from the command line)
            bis_genericio.runPipelineModule({ 'input' : filename, 'output' :  outputFilename, 'odir' : odirFilename }, true).then( () => {
                bis_webutil.createAlert('Pipeline Makefile created.');
            });
        });

        function splitByPathSeparator(filename) {
            if (filename.includes('/')) { return  { 'name' : filename.split('/'), 'sep' : '/'}; }
            if (filename.includes('\\')) { return  { 'name' : filename.split('\\'), 'sep' : '\\' }; }
        }
    }

    /**
     * Imports a filename or set of filenames from disk and returns them to be listed in the modal.
     * 
     * @param {String} f - A filename or a set of filenames.
     * @returns The set of filenames.
     */
    importInputsFromDisk(f) {
        console.log('f', f);

        if (this.pipelineInputs) {
            bootbox.confirm({
                'size': 'small',
                'message': 'There are already inputs defined for this pipeline. Replace the existing inputs with these, or add them to the end?',
                'buttons': {
                    'confirm': {
                        'label': 'Add',
                        'className': 'btn-success'
                    },
                    'cancel': {
                        'label' :  'Replace',
                        'className': 'btn-warning'
                    } 
                },
                'callback' : (add) => {
                    if (add) {
                        this.pipelineInputs = Array.isArray(f) ? this.pipelineInputs.concat(f) : this.pipelineInputs.concat([f]);
                    } else {
                        this.pipelineInputs = Array.isArray(f) ? f : [f];
                    }

                    console.log('pipeline inputs', this.pipelineInputs);
                }
            });
        } else {
            this.pipelineInputs = Array.isArray(f) ? f : [f];
        }

        this.updateInputListElement();    
    }

    updateInputListElement() {

    }

    /**
     * Creates a list item to represent an entry in the current saved pipeline. 
     * 
     * @param {String} moduleName - The name of a BioImageSuite Web module. 
     * @returns A formatted bootstrap list item.
     */
    createPipelineListItem(moduleName) {
        let listItemId = bis_webutil.getuniqueid();
        let listItem = $(`<li id='${listItemId}' class='list-group-item bisweb-pipeline-list-item'>${moduleName}</li>`);
        listItem.on('click', (e) => {
            e.preventDefault(); 
            e.stopPropagation();
            this.openModuleEditingModal(listItem);
        });

        return listItem;
    }

    /**
     * Opens a small bootstrap modal to edit the parameters of a module in the currently saved pipeline. 
     * 
     * @param {JQuery} item - A Bootstrap-formatted list item containing the name of a BioImageSuite Web module.
     */
    openModuleEditingModal(item) {
        let name = $(item).html();
        let modal = bis_webutil.createmodal(`Change parameters for ${name}`, 'modal-sm');

        //generate custom element gui with current params 
        //note that index in visual list will match index in internal list, so we can determine which internal list item to use by finding this element in the visual list
        let listItems = $('#bisweb-panel-pipeline').find('.bisweb-pipeline-list').children();
        let index = null;

        for (let i = 0; i < listItems.length; i++) {
            if ($(listItems[i]).attr('id') === $(item).attr('id')) { index = i; i = listItems.length; }
        }

        let baseMod = moduleIndex.getModule(this.modules[index].name);
        let customModule;

        //modal has to be displayed before width can be read.
        modal.dialog.on('shown.bs.modal', () => {
            //modal body padding is 20px by default
            let width = $(modal.body).outerWidth() - 40;
            console.log('width', width);
            customModule = bisweb_custommodule.createCustom(null, this.algocontroller, baseMod, { 'numViewers' : 0, 'dual' : false, 'paramsMargin' : '0px', 'buttonsMargin' : '0px', 'width' : width });
            modal.body.append(customModule.panel.widget);
            customModule.createOrUpdateGUI( {'width' : width});
            customModule.updateParams(this.savedParameters[index]);
        });
        

        //add save button to modal
        modal.footer.empty();
        let saveButton = bis_webutil.createbutton({ 'name' : 'Save', 'type' : 'btn-primary' });
        saveButton.on('click', () => {
            this.modules[index].module = customModule;
            console.log('module', this.modules[index]);
            modal.dialog.modal('hide');
        });

        let closeButton = bis_webutil.createButton({ 'name' : 'Close'});
        closeButton.on('click', () => {
            modal.dialog.modal('hide');
        });

        modal.footer.prepend(saveButton);
        modal.dialog.modal('show');
    }
}

//Adds 'bisweb-centered-customelement' class to custom element
let centerCustomElement = (widget) => { 
    $(widget).find('.bisweb-customelement-body').addClass('bisweb-centered');
    $(widget).find('.bisweb-customelement-footer').addClass('bisweb-centered');
};

bis_webutil.defineElement('bisweb-filetreepipeline', FileTreePipeline);
module.exports = FileTreePipeline;
