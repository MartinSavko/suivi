#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyTango
import re
import time
import os
import copy

def loadSnapshot(filename):
    f = open(filename)
    text = f.read()
    f.close()
    return text

def alignLists(listToSort, referenceList):
    returnList = []
    for item in referenceList:
        if item in listToSort:
            returnList.append(item)
        else:
            print 'item %s not in listToSort' % item
    return returnList

def getAttributesFromExample(fname="/927bis/ccd/gitRepos/suivi/SuiviLigne_18-03-2014_13h57.txt"):
    exampleAttributes = []
    f = open(fname)
    fr = f.readlines()
    f.close()
    for item in fr[4:]:
        exampleAttributes.append(item.split(';')[0])
    return exampleAttributes

def orderAttributes(attributes, method='example'):
    if method = 'alphabet':
        orderedAttributes = copy.deepcopy(attributes)
        orderedAttributes.sort()
    elif method = 'example':
        attributesFromExample = getAttributesFromExample()
        orderedAttributes = alignLists(attributes, attributesFromExample)
    return orderedAttributes

def getAttributes(text):
    searchString = 'CompleteName=\"([^"]*)\"'
    attributes = re.findall(searchString, text)
    return attributes
    
def getTemplate(text, attributes):
    template = text
    t = 'Time=\"([^"]*)\"'
    timesegment = re.findall(t, template)[0]
    template = template.replace(timesegment, '{timestamp}')
    p = 'path=\"([^"]*)\"'
    pathsegment = re.findall(p, template)[0]
    template = template.replace(pathsegment, '{path}')
    i = 'Id=\"([^"]*)\"'
    idsegment = re.findall(i, template)[0]
    template = template.replace(idsegment, '{id}')
    
    for attribute in attributes:
        #s = '<Attribute.*' + attribute + '.*\n(<ReadValue.*>\n.*\n<\/ReadValue>)\n(<WriteValue.*>\n.*\n<\/WriteValue>)\n<\/Attribute>'
        #k = '(<Attribute.*' + attribute + '.*\n(<ReadValue.*>\n.*\n<\/ReadValue>)\n(<WriteValue.*>\n.*\n<\/WriteValue>)\n<\/Attribute>)'
        l = '(<Attribute.*' + attribute + '.*\n<ReadValue.*>\n.*\n<\/ReadValue>\n<WriteValue.*>\n.*\n<\/WriteValue>\n<\/Attribute>)'
        r = '(<ReadValue.*>(\n.*\n)<\/ReadValue>)'
        w = '(<WriteValue.*>(\n.*\n)<\/WriteValue>)'
        naw = '(<WriteValue notApplicable="(.*)">(\n.*\n)<\/WriteValue>)'
        nar = '(<ReadValue notApplicable="(.*)">(\n.*\n)<\/ReadValue>)'
        
        segment = re.findall(l, text)[0]
        
        real_write, write_value_string = re.findall(w, segment)[0]
        real_read, read_value_string = re.findall(r, segment)[0]
        
        template_write_segment = real_write.replace(write_value_string, '\n{' + attribute.replace('.', '_') + '_write_value}\n')
        template_read_segment = real_read.replace(read_value_string, '\n{' + attribute.replace('.', '_') + '_read_value}\n')
        
        template_segment = segment.replace(real_write, template_write_segment)
        template_segment = template_segment.replace(real_read, template_read_segment)
        
        template = template.replace(segment, template_segment)
    return template
    
def getTemplateAndValues(text, attributes, path):
    tiktak = time.time()

    snap_template = text
    t = 'Time=\"([^"]*)\"'
    timesegment = re.findall(t, snap_template)[0]
    snap_template = snap_template.replace(timesegment, '{timestamp}')
    p = 'path=\"([^"]*)\"'
    pathsegment = re.findall(p, snap_template)[0]
    snap_template = snap_template.replace(pathsegment, '{path}')
    
    table_template = ''
    table_template = 'Snapshot ID;Snapshot Time;Linked context ID\n'
    fstring = '%s;%s;%s\n\n'
    table_template += fstring % ('{id}', '{formatedtime}', '23')
    toWrite = ('Attributes', 'Write Value', 'Read Value', 'DELTA')
    fstring = '%s;%s;%s;%s\n' 
    table_template += fstring % toWrite
    
    values = {}
    values['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    values['path'] = path
    values['timestamp'] = time.ctime(tiktak)
    values['formatedtime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tiktak))
    values['timeTitle'] = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(tiktak))
    values['time'] = tiktak
    values['id'] = tiktak
    
    for attribute in attributes:
        #s = '<Attribute.*' + attribute + '.*\n(<ReadValue.*>\n.*\n<\/ReadValue>)\n(<WriteValue.*>\n.*\n<\/WriteValue>)\n<\/Attribute>'
        #k = '(<Attribute.*' + attribute + '.*\n(<ReadValue.*>\n.*\n<\/ReadValue>)\n(<WriteValue.*>\n.*\n<\/WriteValue>)\n<\/Attribute>)'
        l = '(<Attribute.*' + attribute + '.*\n<ReadValue.*>\n.*\n<\/ReadValue>\n<WriteValue.*>\n.*\n<\/WriteValue>\n<\/Attribute>)'
        r = '(<ReadValue.*>(\n.*\n)<\/ReadValue>)'
        w = '(<WriteValue.*>(\n.*\n)<\/WriteValue>)'
        
        segment = re.findall(l, text)[0]
        
        real_write, write_value_string = re.findall(w, segment)[0]
        real_read, read_value_string = re.findall(r, segment)[0]
        template_write_segment = real_write.replace(write_value_string, '\n{' + attribute.replace('.', '_') + '_write_value}\n')
        template_read_segment = real_read.replace(read_value_string, '\n{' + attribute.replace('.', '_') + '_read_value}\n')
        template_segment = segment.replace(real_write, template_write_segment)
        template_segment = template_segment.replace(real_read, template_read_segment)
        snap_template = snap_template.replace(segment, template_segment)
        
        table_template += fstring % (attribute, 
                                    '{' + attribute.replace('.', '_') + '_write_value}', 
                                    '{' + attribute.replace('.', '_') + '_read_value}', 
                                    '{' + attribute.replace('.', '_') + '_delta}')
        
        naw = '<WriteValue notApplicable="(.*)">\n.*\n<\/WriteValue>'
        nar = '<ReadValue notApplicable="(.*)">\n.*\n<\/ReadValue>'
        
        nawv = re.findall(naw, segment)[0]
        narv = re.findall(nar, segment)[0]
        
        ap = PyTango.AttributeProxy(attribute)
        read = ap.read()
        write_value = read.w_value
        read_value = read.value
        
        if read_value is not None and write_value is not None:
            if read_value - write_value > 0.01 * read_value:
                delta = read_value - write_value
        else:
            delta = ''
        
        if read_value is None:
            read_value = ''
        if write_value is None:
            write_value = read_value
        
        
        if nawv == 'false':
            values[attribute.replace('.', '_') + '_write_value'] = write_value
        else:
            values[attribute.replace('.', '_') + '_write_value'] = ''
            delta = ''
            
        if narv == 'false':
            values[attribute.replace('.', '_') + '_read_value'] = read.value
        else:
            values[attribute.replace('.', '_') + '_read_value'] = ''
            delta = ''
        
        values[attribute.replace('.', '_') + '_delta'] = delta
        
    return snap_template, table_template,  values
    

    
def printAttributeValues(attributes):
    for attribute in attributes:
        ap = PyTango.AttributeProxy(attribute)
        read = ap.read()
        print '%s %s %s' % (attribute, str(read.value), str(read.w_value))
        
def getValues(attributes):
    values = {}
    tiktak = time.time()
    values['timestamp'] = time.ctime(tiktak)
    values['formatedtime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tiktak))
    values['timeTitle'] = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(tiktak))
    values['time'] = tiktak
    values['id'] = tiktak
    for attribute in attributes:
        ap = PyTango.AttributeProxy(attribute)
        read = ap.read()
        write_value = read.w_value
        read_value = read.value
        
        if read_value is not None and write_value is not None:
            if read_value - write_value > 0.01 * read_value:
                delta = read_value - write_value
        else:
            delta = ''
        values[attribute.replace('.', '_') + '_delta'] = delta
        
        if read_value is None:
            read_value = ''
        if write_value is None:
            write_value = read_value
            
        values[attribute.replace('.', '_') + '_write_value'] = write_value
        values[attribute.replace('.', '_') + '_read_value'] = read.value
    return values

def getTableTemplate(attributes):
    table_template = 'Snapshot ID;Snapshot Time;Linked context ID\n'
    fstring = '%s;%s;%s\n\n'
    table_template += fstring % ('{id}', '{formatedtime}', '23')
    toWrite = ('Attributes', 'Write Value', 'Read Value', 'DELTA')
    fstring = '%s;%s;%s;%s\n' 
    table_template += fstring % toWrite
    for attribute in attributes:
        table_template += fstring % (attribute, 
                              '{' + attribute.replace('.', '_') + '_write_value}', 
                              '{' + attribute.replace('.', '_') + '_read_value}', 
                              '{' + attribute.replace('.', '_') + '_delta}')
    return table_template
                              

def saveTable(directory, template, values):
    directory = os.path.join(directory, 'Tables')
    fname = os.path.join(directory, 'SuiviLigne_' + values['timeTitle'] + '.txt')
    f = open(fname, 'w')
    f.write(template.format(**values))
    f.close()

def saveSnapshot(directory, template, values):
    directory = os.path.join(directory, 'Snapshots')
    fname = os.path.join(directory, 'snapshot_'+ values['timeTitle'] + '.snap')
    f = open(fname, 'w')
    f.write(template.format(**values))
    f.close()
    
def synchronize():
    os.system('rsync -avz /927bis/ccd/Database/Tables /927bis/ccd/Database/Snapshots srv2:/nfs/ruche-proxima2a/proxima2a-soleil/SuiviLigne/')
    
def main():    
    import optparse
    usage = "usage: %prog --file <filename>"
    parser = optparse.OptionParser(usage = usage)

    parser.add_option("-f", "--filename", default='/927bis/ccd/gitRepos/suivi/sn23_992.snap', help="Snapshot file that will serve as a template.")
    parser.add_option("-e", "--example", default='/927bis/ccd/gitRepos/suivi/SuiviLigne_18-03-2014_13h57.txt', help="Example file with ordered attributes.")
    parser.add_option("-t", "--template", help="Template file.")
    parser.add_option("-o", "--output", default='/927bis/ccd/Database', help="Output file directory.")
    
    (options, args) = parser.parse_args()
    print 'options, args', options, args
    
    directory = options.output
    filenameStart = options.filename[:-5]
    
    path = os.path.join(directory, filenameStart, '.snap')
    text = loadSnapshot(options.filename)
    attributes = getAttributes(text)
    attributes = orderAttributes(attributes) 
    #print 'attributes', attributes
    snap_template, table_template, values = getTemplateAndValues(text, attributes, path)
    #print 'values', values
    
    #f = open(filenameStart + '_snap.tmpl', 'w')
    #f.write(snap_template)
    #f.close()
    
    f = open(filenameStart + '_table.tmpl', 'w')
    f.write(table_template)
    f.close()
    
    saveSnapshot(directory, snap_template, values)
    saveTable(directory, table_template, values)
    synchronize()
    
if __name__ == '__main__':
    main()