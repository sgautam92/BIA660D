from __future__ import print_function
import re
import spacy

from pyclausie import ClausIE


nlp = spacy.load('en')
re_spaces = re.compile(r'\s+')


class Person(object):
    def __init__(self, name, likes=None, has=None, travels=None):
        """
        :param name: the person's name
        :type name: basestring
        :param likes: (Optional) an initial list of likes
        :type likes: list
        :param dislikes: (Optional) an initial list of likes
        :type dislikes: list
        :param has: (Optional) an initial list of things the person has
        :type has: list
        :param travels: (Optional) an initial list of the person's travels
        :type travels: list
        """
        self.name = name
        self.likes = [] if likes is None else likes
        self.has = [] if has is None else has
        self.travels = [] if travels is None else travels

    def __repr__(self):
        return self.name


class Pet(object):
    def __init__(self, pet_type, name=None):
        self.name = name
        self.type = pet_type


class Trip(object):
    def __init__(self):
        self.departs_on = None
        self.departs_to = None
        self.departs_time=departs_time

persons = []
pets = []
trips = []


def get_data_from_file(file_path='./assignment_01.data'):
    with open(file_path) as infile:
        cleaned_lines = [line.strip() for line in infile if not line.startswith(('$$$', '###', '===',))]

    return cleaned_lines


def select_person(name):
    for person in persons:
        if person.name == name:
            return person


def add_person(name):
    person = select_person(name)

    if person is None:
        new_person = Person(name)
        persons.append(new_person)

        return new_person

    return person


def select_pet(name):
    for pet in pets:
        if pet.name == name:
            return pet


def add_pet(type, name=None):
    pet = None

    if name:
        pet = select_pet(name)

    if pet is None:
        pet = Pet(type, name)
        pets.append(pet)

    return pet


def get_persons_pet(person_name):

    person = select_person(person_name)

    for thing in person.has:
        if isinstance(thing, Pet):
            return thing



def process_relation_triplet(triplet):
    """
    Process a relation triplet found by ClausIE and store the data

    find relations of types:
    (PERSON, likes, PERSON)
    (PERSON, has, PET)
    (PET, has_name, NAME)
    (PERSON, travels, TRIP)
    (TRIP, departs_on, DATE)
    (TRIP, departs_to, PLACE)

    :param triplet: The relation triplet from ClausIE
    :type triplet: tuple
    :return: a triplet in the formats specified above
    :rtype: tuple
    """

    sentence = triplet.subject + ' ' + triplet.predicate + ' ' + triplet.object

    doc = nlp(unicode(sentence))
    global root
    for t in doc:
        if t.pos_ == 'VERB' and t.head == t:
            root = t
        # elif t.pos_ == 'NOUN'

    # also, if only one sentence
    # root = doc[:].root


    """
    CURRENT ASSUMPTIONS:
    - People's names are unique (i.e. there only exists one person with a certain name).
    - Pet's names are unique
    - The only pets are dogs and cats
    - Only one person can own a specific pet
    - A person can own only one pet
    """


    # Process (PERSON, likes, PERSON) relations
    if root.lemma_ == 'like':
        if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON'] and triplet.object in [e.text for e in doc.ents if e.label_ == 'PERSON']:
            s = add_person(triplet.subject)
            o = add_person(triplet.object)
            s.likes.append(o)

    if root.lemma_ == 'be' and triplet.object.startswith('friends with'):
        fw_doc = nlp(unicode(triplet.object))
        with_token = [t for t in fw_doc if t.text == 'with'][0]
        fw_who = [t for t in with_token.children if t.dep_ == 'pobj'][0].text
        # fw_who = [e for e in fw_doc.ents if e.label_ == 'PERSON'][0].text

        if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON'] and fw_who in [e.text for e in doc.ents if e.label_ == 'PERSON']:
            s = add_person(triplet.subject)
            o = add_person(fw_who)
            s.likes.append(o)
            o.likes.append(s)


    # Process (PET, has, NAME)
    if triplet.subject.endswith('name') and ('dog' in triplet.subject or 'cat' in triplet.subject):
        obj_span = doc.char_span(sentence.find(triplet.object), len(sentence))

        # handle single names, but what about compound names? Noun chunks might help.
        if len(obj_span) == 1 and obj_span[0].pos_ == 'PROPN':
            name = triplet.object
            subj_start = sentence.find(triplet.subject)
            subj_doc = doc.char_span(subj_start, subj_start + len(triplet.subject))

            s_people = [token.text for token in subj_doc if token.ent_type_ == 'PERSON']
            assert len(s_people) == 1
            s_person = select_person(s_people[0])

            s_pet_type = 'dog' if 'dog' in triplet.subject else 'cat'

            pet = add_pet(s_pet_type, name)

            s_person.has.append(pet)


def preprocess_question(question):
    # remove articles: a, an, the

    q_words = question.split(' ')

    # when won't this work?
    for article in ('a', 'an', 'the'):
        try:
            q_words.remove(article)
        except:
            pass

    return re.sub(re_spaces, ' ', ' '.join(q_words))


def has_question_word(string):
    # note: there are other question words
    for qword in ('who', 'what'):
        if qword in string.lower():
            return True

    return False



def main():
    sents = get_data_from_file()

    cl = ClausIE.get_instance()

    triples = cl.extract_triples(sents)

    for t in triples:
        r = process_relation_triplet(t)
        # print(r)

    question = ' '
    while question[-1] != '?':
        question = raw_input("Please enter your question: ")

        if question[-1] != '?':
            print('This is not a question... please try again')

    q_trip = cl.extract_triples([preprocess_question(question)])[0]

    # (WHO, has, PET)


 # Q.1> Who has a <pet type>?
    if q_trip.subject.lower() == 'who' and (q_trip.object == 'dog' or q_trip.object == 'cat'):
        answer = '{} has a {} named {}.'
        print()
        for person in persons:
            pet = get_persons_pet(person.name)
            if pet and pet.type == 'dog' and q_trip.object == 'dog':
                print(answer.format(person.name, 'dog', pet.name))
            elif pet and pet.type == 'cat' and q_trip.object == 'cat':
                print(answer.format(person.name,'cat',pet.name))
    # Q.2> Does <person> like <person>?
    elif 'does' in q_trip.subject.lower() and 'like' in q_sentence:
        answer = '{} likes {}'
        print()
        person_a = [token.text for token in q_doc.ents if token.label_== 'PERSON'][0]
        select_a = select_person(person_a)
        person_b = q_trip.object
        select_b = select_person(person_b)
        if select_b in select_a.likes:
            print(answer.format(select_a,select_b))
        else:
            print('No relation given')

    # Q.3> Who is [going to|flying to|traveling to] <place>?
    elif q_trip.subject.lower() == 'who' and 'GPE' in [e.label_ for e in q_doc.ents]:
        answer = '{} is traveling to {}'
        print()
        check = 0
        travel_d = str([t.text for t in q_doc.ents if t.label_=="GPE"][0])
        for person in persons:
            if travel_d in [trip.departs_to for trip in person.travels]:
                print(answer.format(person.name,travel_d))
                check = 1
        if check==0:
            print(answer.format('Nobody',travel_d))

    # Q.4> When is <person> [going to|flying to|traveling to] <place>?
    elif 'when' in q_sentence.lower() and 'GPE' in [e.label_ for e in q_doc.ents]:
        answer = '{} is traveling to {} on {}'
        print()
        person_t = str([t.text for t in q_doc.ents if (t.label_=="PERSON" or t.label_=="ORG")][0])
        dest = str([t.text for t in q_doc.ents if t.label_=="GPE"][0])
        check=0
        for person in persons:
            if person_t == person.name:
                if dest in [trip.departs_to for trip in person.travels]:
                    print(answer.format(person_t, dest, trip.departs_on))
                    check =1
        if check==0:
            print(person_t+' is NOT traveling to '+dest+' anytime soon')
    # Q.5> Who likes <person>?
    elif ('who' in q_sentence.lower() and ('ORG' in [e.label_ for e in q_doc.ents] or 'PERSON' in [e.label_ for e in q_doc.ents])) and q_trip.predicate=='likes':
        person_l = str([t.text for t in q_doc.ents if (t.label_=='PERSON' or t.label_=='ORG')][0])
        like_l = []
        for person in persons:
            for personl in person.likes:
                    if person_l==personl.name:
                        like_l.append(person.name)
        if len(like_l)>0:
            print(person_l+' is liked by the following people:')
            for p in like_l:
                print(p)
        elif len(like_l)==1:
            print(person_l+' is liked by '+like_l[0])
        else:
            print('Nobody likes '+person_l)

    # Q.6> Who does <person> like?
    elif 'who' in q_sentence.lower() and 'does' in q_sentence.lower():
        person_lb = str([t.text for t in q_doc.ents if (t.label_=='PERSON' or t.label_=='ORG')][0])
        like_lb = []
        for person in persons:
            if person_lb==person.name:
                for p in person.likes:
                    like_lb.append(p.name)
        if len(like_lb)==1:
            print(person_lb+' likes '+like_lb[0])
        elif len(person_lb)>1:
            print(person_lb+' like the following people:')
            for q in like_lb:
                print(q)
        else:
            print('Nobody likes '+person_lb)
    else:
        print("I don't know")


if __name__ == '__main__':
    main()

