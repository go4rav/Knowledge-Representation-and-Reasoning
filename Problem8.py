#Import the required modules
#pip install xmltodict
#pip install dict2xml
import xmltodict
from dict2xml import dict2xml
import pprint
import json
import collections
 
f= open("output.txt","w")



#After capturing the transitive relation and getting the  output dictionary, we need to save it text file.

def save(output_dict):
    # Function to save the data being read from the dict into an output text file
    ordered_dict = collections.OrderedDict(output_dict)
    output_list = output_dict['KB']['Class']
    #Parse class by class and modify tags based on relevant tags

    # So we read each class from the dictionary,
    for ele in output_list:
        string = ''
        keys=ele.keys()
        mod = False

        # if there is a concept pair, we write in the output file
        if 'CONCEPT' in keys:
            f.write('Class: '+ele['CONCEPT']+'\n')

        # if there exists a subclassof relation
        if 'SubClassOf' in keys:
            string = '        SubClassOf: ' 
            cons = ele['SubClassOf']
            flag = ''

            # then it could be subclassof one or many concepts like TA can be subclass of student and teacher, this code handles that
            if 'CONCEPT' in cons:
                concepts = cons['CONCEPT']
                concepts = [concepts] if isinstance(concepts, str) else concepts
                i= 0


                for concept in concepts:
                    if i ==1:
                        string = string + ','
                    string = string + flag + concept
                    i = i+1
                    mod = True

            # the concept may be subclass of not of the concept

            if 'NOT' in ele['SubClassOf']:
                flag = ' not '
                cons = ele['SubClassOf']['NOT']
                if 'CONCEPT' in cons:
                    concepts = cons['CONCEPT']
                    concepts = [concepts] if isinstance(concepts, str) else concepts
                    i= 0
                    for concept in concepts:
                        if mod== True:
                            string = string + ','
                            mod = False
                        if i ==1:
                            string = string + ','
                        string = string + flag + concept
                        i = i+1

            # if there is a  exists tag  in subclassof, we look for the role and the concept and there can be multiple of such roles.
                
            if 'EXISTS' in ele['SubClassOf']:
                flag=''
                cons = ele['SubClassOf']['EXISTS']
                elements = cons
                elements = [elements] if isinstance(elements, dict) else elements
                for element in elements:
                    role = element['ROLE']
                    if 'NOT' in cons:
                        flag = ' not '
                        element =  ele['SubClassOf']['EXISTS']['NOT']
                    concept = element['CONCEPT']

                    # we store it in a string and then write it in the output and after that we use parser to convert the text file into output xml.
                    string = string + ' , '+ role + ' some '+ flag +  concept

            f.write(string+'\n')




def convertXMLToDict(file):

    # Parse the XML document and save it into a dictionary
    my_dict = xmltodict.parse(my_xml)   
    return my_dict['KB']['Class']

def processTags(class_list):
    # Function to take the dictionary with the XML data and obtain the subsumption hierarchy
    output_list = []
    concept_subsumptions = {}
    concept_equivalence = {}
    concept_other = {}

    for pair in class_list:
        #Initializing with empty lists for the class currently being processed
        concept_subsumptions[str(pair['CONCEPT'])] = []
        concept_equivalence[str(pair['CONCEPT'])] = []
        concept_other[str(pair['CONCEPT'])] = []

        if 'SubClassOf' in pair:
            #Checking if the current class is subclass of some other class
            if 'CONCEPT' in pair['SubClassOf']:
                concept_subsumptions[str(pair['CONCEPT'])].append(pair['SubClassOf'])
                # Add all other classes for which this class is a subclass
                for concept in concept_subsumptions[str(pair['SubClassOf']['CONCEPT'])]:
                    concept_subsumptions[str(pair['CONCEPT'])].append(concept)

                '''Add these lines of code to include additional subsumption (NOT class, etc)'''
                for concept in concept_equivalence[str(pair['SubClassOf']['CONCEPT'])]:
                    concept_equivalence[str(pair['CONCEPT'])].append(concept)
                # for concept in concept_other[str(pair['SubClassOf']['CONCEPT'])]:
                #     concept_other[str(pair['CONCEPT'])].append(concept)
            else:
                concept_other[str(pair['CONCEPT'])].append(pair['SubClassOf'])


        if 'EquivalentTo' in pair:
            #Checking if the current class is equivalent to some other class
            if 'CONCEPT' in pair['EquivalentTo']['AND']:
                concept_equivalence[str(pair['CONCEPT'])].append(pair['EquivalentTo']['AND'])
                #Find all the concepts in the EquivalentTo  / AND tag
                concepts = pair['EquivalentTo']['AND']['CONCEPT']
                concepts = [concepts] if isinstance(concepts, str) else concepts
                # Add all the (transitive) subsumption relations from the parents information
                for concept in concepts:
                    #Read subsumptions
                    concept_subsumptions[str(pair['CONCEPT'])].append({'CONCEPT':str(concept)})
                    for concept2 in concept_subsumptions[str(concept)]:
                        concept_subsumptions[str(pair['CONCEPT'])].append(concept2)
                    concept_subsumptions[str(pair['CONCEPT'])].remove({'CONCEPT':str(concept)})

                    #Read data from equivalence relations
                    concept_equivalence[str(pair['CONCEPT'])].append({'CONCEPT':str(concept)})
                    for concept2 in concept_equivalence[str(concept)]:
                        concept_equivalence[str(pair['CONCEPT'])].append(concept2)
                    concept_equivalence[str(pair['CONCEPT'])].remove({'CONCEPT':str(concept)})

                    #Read data with other tags which need to be subsumed
                    concept_other[str(pair['CONCEPT'])].append({'CONCEPT':str(concept)})
                    for concept2 in concept_other[str(concept)]:
                        concept_other[str(pair['CONCEPT'])].append(concept2)
                    concept_other[str(pair['CONCEPT'])].remove({'CONCEPT':str(concept)})

                    
            else:
                concept_other[str(pair['CONCEPT'])].append(pair['EquivalentTo']['AND'])

    #Second pass to add the subclass and equivalence relations inferred above into a new dictionary as K-V pairs 
    for pair in class_list:
        #Add the data from other tagss wrt Subsumption
        for others in concept_other[pair['CONCEPT']]:
            new_pair = {}
            new_pair['CONCEPT'] = pair['CONCEPT']
            new_pair['SubClassOf'] = others
            output_list.append(new_pair)
        #Add data wrt equivalence relation
        for equivalence in concept_equivalence[pair['CONCEPT']]:
            new_pair = {}
            new_pair['CONCEPT'] = pair['CONCEPT']
            new_pair['SubClassOf'] = equivalence
            output_list.append(new_pair)
            #Add data wrt subsumption relation
        for concept in list({concept_subs['CONCEPT']:concept_subs for concept_subs in concept_subsumptions[pair['CONCEPT']]}.values()):
            new_pair = {}
            new_pair['CONCEPT'] = pair['CONCEPT']
            new_pair['SubClassOf'] = concept
            output_list.append(new_pair)       
        if ('EquivalentTo' not in pair) and ('SubClassOf' not in pair):
            output_list.append(pair)

    #Save final contents onto the output_dict
    output_dict_class = {}
    output_dict_class['Class'] = output_list
    output_dict = {}
    output_dict['KB'] = output_dict_class
    save(output_dict)
    #Convert output dict to XML
    output_xml = dict2xml(output_dict)
    return output_xml

def saveXMLOutput(output_xml):
    '''Function to convert dictionary K-V pairs to an XML file'''
    f =  open("output_file.xml", "w")
    f.write(output_xml)
    f.close()



# Open the file and read the contents
with open('inputUniv.xml', 'r', encoding='utf-8') as file:
    my_xml = file.read()

#Get dictionary representation of the XML
class_dict = convertXMLToDict(my_xml)

#Convert to dict
class_list = json.loads(json.dumps(class_dict))

#Convert tags and replace any not "Subclass" or not "Concept"
output_xml = processTags(class_list)

pprint.pprint(output_xml)

#Save output to file
saveXMLOutput(output_xml)


