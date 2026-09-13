import math
import argparse
import pickle
import csv

global IndexFile

# file 내에 node 1개가 차지하는 byte 수
def node_offset_size(degree):
    return 512 + 32* degree

# 최소 node 사이즈 조건을 만족하기 위해 node에 존재해야 하는 최소 key 개수
def minimum_key_number(degree):
    return math.ceil((degree-1)/2)


class Node:
    def __init__ (self, degree, offset=None):
        self.degree = degree # 최대 child node의 개수
        self.offset = offset # file 내의 offset (file로부터 아직 load되지 못했거나 새로 생성 후 save되지 못한 경우 none)
        self.keys = []
        self.pointers = []
        # leaf node의 경우 데이터를(pointer), non-leaf node의 경우 자식 노드를 가리키는 pointer 값(offset)을 저장함
        # 따라서 leaf node일 경우 keys 배열과 동일한 길이, non-leaf node의 경우 keys 배열보다 1 긴 길이
       
        self.next = None # leaf node에서 다음 noded를 가리키는 pointer (offset 값)
        self.isLeaf = True # leaf node인지 여부
        self.parent = None # parent node를 가리키는 pointer (offset 값)
    

    #------------------------------------ File I/O 관련 함수 ------------------------------------#

    # 파일로부터 node를 읽어오는 함수
    def load_from_file(self, offset):
        global IndexFile
        IndexFile.seek(offset)
        data =  pickle.load(IndexFile)
        self.degree = int(data.degree)
        self.offset = offset
        self.keys = data.keys
        self.pointers = data.pointers
        self.next = data.next
        self.isLeaf = data.isLeaf
        self.parent = data.parent

    # 기존에 저장되어 있던 위치에 node의 변경 내용을 저장하는 함수
    def save_to_file(self):
        if(self.next != None and type(self.next)!=int):
            self.next = self.next.offset

        global IndexFile
        IndexFile.seek(self.offset)
        pickle.dump(self, IndexFile)
        '''
        print("\n[디버깅] file에 node 정보를 수정했습니다. 수정된 node 정보를 출력합니다")
        print(f"         degree : {self.degree} , offset : {self.offset}")
        print(f"         keys : {self.keys}")
        print(f"         pointers: {self.pointers}")
        print(f"         next : {self.next}, isLeaf : {self.isLeaf} , parent : {self.parent}\n")
        '''
        

    
    # 새롭게 파일에 node를 저장하는 함수
    # 파일의 맨 마지막에 저장 (각 노드당 512 + 32* degree byte의 자리를 차지하도록 함)
    def write_to_file(self):
        if(self.offset != None):
            # print("[오류] 이미 file에 저장되어 있는 node입니다. save_to_file 함수를 쓰는 것을 권장합니다")
            self.save_to_file()
            return

        if(self.next != None and type(self.next)!=int):
            self.next = self.next.offset

        IndexFile.seek(0, 2) # 파일의 맨 끝으로 이동
        now = IndexFile.tell() # 현재 file pointer의 위치

        nextOffset = math.ceil((now-512)/node_offset_size(self.degree))*node_offset_size(self.degree) + 512 # 다음 node가 저장될 위치 계산
        self.offset = nextOffset # 객체에 offset 저장
        IndexFile.seek(nextOffset)
        pickle.dump(self, IndexFile)
        '''
        print("\n[디버깅] file에 새로운 node를 추가했습니다. 새로 추가된 node 정보를 출력합니다")
        print(f"         degree : {self.degree} , offset : {self.offset}")
        print(f"         keys : {self.keys}")
        print(f"         pointers: {self.pointers}")
        print(f"         next : {self.next}, isLeaf : {self.isLeaf} , parent : {self.parent}\n")
        '''
    
    # 특정 offset에 새로 node를 저장하는 함수
    # create에서 root node를 512에 저장하기 위해 만든 함수
    # 안정성을 위해 외의 상황에서는 사용하지 않는 것을 권장
    def write_to_file_with_offset(self, offset):
        global IndexFile
        IndexFile.seek(offset)
        pickle.dump(self, IndexFile)


    #------------------------------- 클래스 내 데이터를 반환해주는 함수들 ------------------------------#

    # 노드가 leaf node인지 여부를 리턴해주는 함수
    def get_isLeaf(self):
        return self.isLeaf


    # 해당 노드의 첫번째 (가장 왼쪽) child node를 리턴해주는 함수
    # child node 정보를 file에서 읽어와 객체화 하여 리턴함
    # 해당 노드가 leaf node이거나 child node를 가지지 않는 경우 0을 리턴함
    def get_first_child(self):
        if(len(self.pointers) == 0):    # 해당 노드가 child node를 갖고 있지 않은 경우 (예외 처리)
            print("해당 노드는 child node를 갖고 있지 않습니다.")
            return 0
        if (self.isLeaf == True):   # 해당 노드가 leaf node인 경우 (예외 처리)
            print("해당 노드는 leaf node로 child node가 존재하지 않습니다.")
            return 0
        
        firstChild = Node(self.degree)
        firstChild.load_from_file(self.pointers[0])
        return firstChild


    # leaf node에서 다음 노드를 리턴해주는 함수
    # 다음 노드 정보를 file에서 읽어와 객체화 하여 리턴해줌
    def get_next_node(self):
        if(self.isLeaf == False):   #leaf node가 아닌 경우 (예외 처리)
            print("해당 노드는 leaf node가 아니므로 next node가 존재하지 않습니다")
            return 0
        nextNode = Node(self.degree)
        nextNode.load_from_file(self.next)
        return nextNode


    # 해당 노드의 첫번째 (가장 왼쪽) key 값을 리턴해주는 함수
    def get_first_key(self):
        if(len(self.keys) == 0):
            print("해당 노드에는 key값이 들어있지 않습니다")
            return 0
        return self.keys[0]
    

    # 현재 노드에 들어있는 key값의 수를 리턴해주는 함수
    def get_node_size(self):
        return len(self.keys)
    

    # 현재 노드의 parent node를 리던해주는 함수
    # indexFile에서 parent node 정보를 읽어와 객체화 하여 리턴해줌
    def get_parent_node(self):
        if(self.parent == None):
            # print("[오류] parent node가 존재하지 않습니다")
            return
        parentNode = Node(self.degree)
        parentNode.load_from_file(self.parent)
        return parentNode

    #------------------------------------------------------------------------------------------#
    #--------------------------------- 기본 함수들 (포괄적으로 사용) ---------------------------------#




    #------------------------------------------------------------------------------------------#
    #------------------------------------- SEARCH 관련 함수들 ------------------------------------#

    # 노드의 모든 key값 출력
    def print_all_keys(self):
        if(len(self.keys) == 0): # 빈 노드인 경우
            # print("[오류] 빈 노드입니다")
            return

        print(str(self.keys[0]), end="")
        for i in range(1, len(self.keys)):
            print(f",{self.keys[i]}", end="")
        print()
        return
        
        
    

    # leaf node 에서 특정 key 값에 해당하는 데이터 (pointer 값)를 리턴해주는 함수
    # 해당 값이 없거나 해당 노드가 leaf node가 아닌 경우 0을 리턴
    # 해당 값이 없는 경우 "NOT FOUND" 리턴
    def get_value (self, key):
        if(self.isLeaf == True): # leaf node인 경우
            for i in range(len(self.keys)):
                if(key == self.keys[i]):
                    return self.pointers[i]
            # 해당 key 값에 해당하는 데이터가 없는 경우
            return "NOT FOUND"
        else: # leaf node가 아닌 경우
            print("해당 노드는 leaf node가 아닙니다.")
            return 0 


    # non-leaf node에서 특정 key 값을 찾기위해 이동해야하는 다음 node 객체를 리턴해주는 함수
    # 현재 노드가 leaf node인 경우 0을 리턴함
    def find_next_route_node (self, key):
        if (self.isLeaf == True): # leaf node인 경우
            print("해당 노드는 leaf node 입니다.")
            return 0
        
        offset = 0
        for i in range(len(self.keys)):
            if(key < self.keys[i]):
                offset = self.pointers[i]
                break

        if(offset == 0):
            offset = self.pointers[len(self.keys)] # 맨 오른쪽 key 값보다도 찾고자 하는 key 값이 큰 경우 맨 오른쪽의 pointer값을 선택
            #print("[디버깅] 맨 마지막 key 값보다도 큽니다. 맨 마지막 child node로 이동합니다")
        nextNode =  Node(self.degree)
        nextNode.load_from_file(offset)
        return nextNode
    

    #------------------------------------------------------------------------------------------#
    #---------------------------------- RANGE SEARCH 관련 함수들 ---------------------------------#


    # startKey 값과 endKey 값 사이의 값들을 출력해주는 함수
    # 각 데이터를 '<key>,<value>\n' 형식으로 한줄씩 출력
    # endKey까지 출력하기 위해 다음 leaf node도 탐색해야 하는 경우 next node 값을 리턴, 그렇지 않은 경우 0을 리턴함
    def print_from_to (self, startKey, endKey):
        for i in range(len(self.keys)):
            if(self.keys[i] > endKey): # 중간에 멈추는경우
                return 0
            if(startKey <= self.keys[i]): # 범위에 포함되는 경우
                print(f"{self.keys[i]},{self.pointers[i]}")

        # 끝까지 전부 출력한 경우

        if(self.next):
            nextNode = Node(self.degree)
            nextNode.load_from_file(self.next)
            return nextNode
        return 0

    #------------------------------------------------------------------------------------------#
    #------------------------------------- INSERT 관련 함수들 ------------------------------------#


    # leaf node에 특정 값을 삽입해주는 함수
    # 삽입에 성공하면 True를 return 함
    # 해당 node가 leaf node가 아니거나, 이미 동일한 key 값이 존재하는 경우 False를 return 함
    def insert_leaf (self, key, value):
        if self.isLeaf == False: #leaf node가 아닌 경우 (예외 처리)
            # print("[오류] 해당 노드는 leaf node가 아닙니다")
            return False
        
        keyLen = len(self.keys)
        if(keyLen == 0):
            self.keys.append(key)
            self.pointers.append(value)
            # print("[디버깅] 빈 leaf node에 ", key, "값을 삽입했습니다.")
            return True

        for i in range(keyLen):
            if key < self.keys[i]:
                self.keys.insert(i, key)
                self.pointers.insert(i, value)
                # print(f"[디버깅] leaf node에 {key} 값을 삽입했습니다. (현재 keys :{self.keys}")
                return True
        # 모든 값보다 큰 경우
        self.keys.append(key)
        self.pointers.append(value)
        # print(f"[디버깅] leaf node에 {key} 값을 삽입했습니다. (현재 keys : {self.keys})")
        return True


    # 현재 node를 root node로 하는 sub tree 내의 가장 작은 key 값을 반환해주는 함수
    def get_subtree_smallest_key (self):
        node_pointer = self
        while(node_pointer.get_isLeaf() != True):   # leeaf node를 찾아감
            node_pointer = node_pointer.get_first_child()
            if(node_pointer == 0):
                # print("[오류] sub tree 내 key 최솟값을 찾기 위해 leaf node까지 가는 중 문제가 발생했습니다.")
                return 0
    
        # leaf node에 도달한 경우 leaf node의 첫번째 key 값을 리턴함
        return node_pointer.get_first_key()


    # non-leaf node에 특정 node를 child node로 삽입해주는 함수
    # 삽입된 child node에 맞게 자동으로 key 값들을 조정해줌
    # 삽입 성공 시 True를 return 함
    def insert_child_node (self, childNode):
        # childNode가 offset으로 넘어온 경우 객체로 변환 후 file로부터 load 해오기
        if(type(childNode) == int):
            childNodeOffset = childNode
            childNode = Node(self.degree)
            childNode.load_from_file(childNodeOffset)

        if(len(self.pointers) == 0): # 빈 노드인 경우
            self.pointers.append(childNode.offset)
            self.isLeaf = False
            childNode.parent = self.offset
            # print("[디버깅] 빈 노드에 child node를 삽입했습니다 (현재 keys :", self.keys, " 삽입된 child keys :", childNode.keys, ")")
            childNode.save_to_file() # parent 정보가 변경되었으므로 변경 사항 file에 저장
            return True
            
        # node 내에서 child node가 삽입되어야 할 위치 찾기    
        index = 0 # childNode가 삽입되어야 할 위치를 저장하는 변수
        smallest = childNode.get_subtree_smallest_key() # child node를 root node로 하는 subtree의 가장 작은 key 값 찾기
        while(index < len(self.keys)):
            if(smallest < self.keys[index]):
                break
            index+=1
        # small < self.keys[index]
        
        # 맨 앞의 key값보다 작은 경우
        if(index == 0):
            firstChildNode = Node(self.degree)
            firstChildNode.load_from_file(self.pointers[0])
            first_node_smallest = firstChildNode.get_subtree_smallest_key()
            if(smallest < first_node_smallest):
                self.pointers.insert(0, childNode.offest)
                self.keys.insert(0, first_node_smallest)
            else:
                self.pointers.insert(1, childNode.offset)
                self.keys.insert(0, smallest)
        else:
            self.pointers.insert(index+1, childNode.offset)
            self.keys.insert(index, smallest)
        self.isLeaf = False
        childNode.parent = self.offset
        # print("[디버깅] 새로운 child node를 삽입했습니다 (node offset : ",  self.offset, "현재 keys :", self.keys, " 삽입된 child keys :", childNode.keys, ")")
        childNode.save_to_file() # parent 정보가 변경되었으므로 변경 사항 file에 저장
        return True

    
    # 현재 노드를 split해 새롭게 만든 노드를 리턴하는 함수
    # [(degree-1)/2]개의 데이터만 남기고 나머지는 새로운 노드를 만들어 이동시킴
    def split_leaf_node(self):
        left_num = minimum_key_number(self.degree) # 남겨둘 데이터의 개수 구하기
        new_node = Node(self.degree)    # 새로운 node 만들기

        new_node.parent = self.parent
        new_node.next = self.next
        self.next = new_node

        # 새로운 노드로 데이터 이동하기
        for i in range (left_num , len(self.keys)):
            new_node.keys.append(self.keys[left_num])
            new_node.pointers.append(self.pointers[left_num])
            del self.keys[left_num]
            del self.pointers[left_num]

        # print("[디버깅] split을 완료했습니다" , self.keys, new_node.keys)
        return new_node
        
    # 현재 노드를 split해 새롭게 만든 노드를 리턴하는 함수
    # [degree/2]개의 child node만 남기고 나머지는 새로운 노드를 만들어 이동시킴
    # child node에 따라 key 값을 조정함
    def split_non_leaf_node(self):
        leftNum = math.ceil(self.degree/2)
        newNode = Node(self.degree)
        newNode.write_to_file() # child node를 삽입할 때에 child node의 parent 값으로 해당 노드의 offset을 지정해야 하므로 일단 file에 저장 후 offset 얻기

        newNode.parent = self.parent
        
        for i in range(leftNum , len(self.pointers)):
            newNode.insert_child_node(self.pointers[leftNum])
            del self.pointers[leftNum]
            del self.keys[leftNum-1]
        return newNode


    #------------------------------------------------------------------------------------------#
    #------------------------------------- DELETE 관련 함수들 ------------------------------------#


    # leaf node에서 특정 key 값의 데이터를 삭제헤주는 함수
    # 삭제 성공 시 true를 실패시 fasle를 리턴
    def delete_leaf_node (self, key):
        if(self.isLeaf == False):
            # print("[오류] 해당 노드는 leaf node가 아닙니다. 이 노드에서는 데이터를 삭제할 수 없습니다.")
            return False
        for i in range(len(self.keys)):
            if(self.keys[i] == key):
                del self.keys[i]
                del self.pointers[i]
                # print("[디버깅]", key, "값을 삭제했습니다. (keys :", self.keys, "values:", self.pointers)
                return True
        # print("[오류] 해당 key 값을 찾을 수 없습니다")
        return False


    # 특정 index의 key 값을 삭제하는 함수
    # 해당 index에 있던 key 값을 리턴함
    def delete_key(self, index):
        if(index >= len(self.keys)):
            # print("[오류] index가 범위를 벗어났습니다. 해당 index의 key 값을 삭제할 수 없습니다.")
            return False
        key = self.keys[index]
        del self.keys[index]
        return key


    # 특정 index의 pointer 값을 삭제하는 함수
    # 해당 index에 있던 pointer 값을 리턴함
    def delete_pointer(self, index):
        if(index >= len(self.pointers)):
            # print("[오류] index가 범위를 벗어났습니다. 해당 index의 pointer 값을 삭제할 수 없습니다.")
            return False
        pointer = self.pointers[index]
        del self.pointers[index]
        return pointer
    
    
    # 두개의 leaf node를 merge하는 함수
    # 현재 노드에 파라미터로 받아온 노드의 값들을 추가함
    def merge_leaf_node(self, siblingNode):
        for i in range(siblingNode.get_node_size()):
            self.insert_leaf(siblingNode.keys[i], siblingNode.pointers[i])
        #print('[디버깅] 두개의 leaf node를 merge 했습니다. keys : ', self.keys , "pointers(values): ", self.pointers)
        return True


    # 두개의 non-leaf node를 merge하는 함수
    def merge_non_leaf_node(self, siblingNode):
        for i in range(len(siblingNode.pointers)):
            self.insert_child_node(siblingNode.pointers[i])
        #print("[디버깅] 두개의 non-leaf node를 merge했습니다. keys : ", self.keys)
        return True


    #------------------------------------------------------------------------------------------#
    #-------------------------------------- DEBUG 관련 함수들 ------------------------------------#
    '''
    def print_node_info(self):
        print("[디버깅] node 정보 - address :", self, "\ndegree: " , self.degree , ", keys :" , self.keys, ", pointers :" , self.pointers, ", isLeaf :", self.isLeaf, ", parent :", self.parent)

    def print_child_keys(self):
        print("\n[디버깅] child key값들을 출력합니다", end=" ")
        print(" 현재 노드 keys : ", self.keys,)
        for i in range(len(self.pointers)):
            print(" ", self.pointers[i].keys, end=" ")
    '''



#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#


class BplusTree:
    def __init__ (self, degree):
        self.root = None
        self.degree = degree
        self.nodeOffset = node_offset_size(degree) # file 내에서 node 1개당 차지하는 사이즈


    #---------------------------------------- File I/O ----------------------------------------#

    def load_bptree_from_file(self):
        global IndexFile
        IndexFile.seek(0)
        data = pickle.load(IndexFile)
        self.root = int(data.root)
        self.degree = int(data.degree)
        self.nodeOffset = int(data.nodeOffset)

    def write_bptree_to_file(self):
        if(type(self.root) != int):
            self.root = self.root.offset
        global IndexFile
        IndexFile.seek(0)
        pickle.dump(self, IndexFile)

    #-------------------------------------- SINGLE SEARCH -------------------------------------#


    # tree에서 key값에 해당하는 데이터 (pointer)값을 찾아 출력 및 반환 해주는 함수
    # search 중 거치는 non leaf node의 모든 key 값들을 출력해줌
    # 해당 key값이 존재하지 않는 경우 0을 리턴함
    def single_search(self, key):
        node_pointer = self.root
        while(node_pointer.get_isLeaf() == False): # leaf node에 도달할때 까지 내려감
            node_pointer.print_all_keys() # non-leaf node의 key 값들 출력
            # print(f"[디버깅] {node_pointer.keys}")
            node_pointer = node_pointer.find_next_route_node(key)
            if(node_pointer == 0): # 문제가 발생한 경우 (예외 처리)
                # print("[오류] search 도중 길을 잃었습니다!")
                return 0
        # leaf node에 도달한 경우 해당 데이터 출력 및 반환
        print(node_pointer.get_value(key))
        return node_pointer.get_value(key)


    #-------------------------------------- RANGE SEARCH --------------------------------------#


    # tree에서 startKey와 endKey 사이에 존재하는 모든 데이터들을 찾아 출력해주는 함수
    # 한개의 데이터 당 '<key>,<value>\n' 형식으로 한줄씩 출력
    def range_search(self, startKey, endKey):
        node_pointer = self.root
        while(node_pointer.get_isLeaf() == False):
            node_pointer = node_pointer.find_next_route_node(startKey)
            if(node_pointer == 0):  # 문제가 발생한 경우 (예외 처리)
                # print("[오류] range search를 위해 시작 leaf node를 찾는 도중 문제가 발생했습니다")
                return 0
        # 시작 leaf node를 찾은 경우 범위 내의 값들을 출력함
        while(node_pointer):
            node_pointer = node_pointer.print_from_to(startKey, endKey)


    #------------------------------------------ INSERT ----------------------------------------#


    # 특정이 key 값이 들어가야 할/특정 key 값이 위치한 leaf node를 찾아 리턴해주는 함수
    # 문제가 발생한 경우 0을 리턴함 (발생해서는 안되는 케이스)
    def find_key_leaf_node (self, key):
        # print("[디버깅] find_key_leaf_node 시작")
        node_pointer = self.root
        while(node_pointer.get_isLeaf() == False): # leaf node에 도달할 때까지 내려감
            # print(f"[디버깅] keys : {node_pointer.keys}, offset : {node_pointer.offset} 인 node를 거쳐갑니다.")
            node_pointer = node_pointer.find_next_route_node(key)
            if(node_pointer == 0): # 문제가 발생한 경우 (예외 처리)
                # print("[오류] key 값에 맞는 적잘한 위치를 찾는 도중 길을 잃었습니다")
                return 0
        # leaf node에 도달한 경우 해당 leaf node를 리턴함
        # print("[디버깅]", node_pointer.keys , "key 값들을 가진 node에 삽입하면 됩니다! (pointers:", node_pointer.pointers, ")")
        return node_pointer


	# b+ tree에 특정 데이터를 삽입하는 함수
	# 삽입에 성공하면 true, 실패하면 false를 리턴함
    def insert (self, key, value):
        insertNode = self.root
        #print(f"[디버깅] insert 함수 시작 (key : {key} , value: {value})")

        # STEP 1 ) 적절한 leaf node에 값 삽입하기
        if(self.root.get_isLeaf() == True):
            # print(f"[디버깅] Root node만 존재합니다")
            # root node만 존재하는 경우
            self.root.insert_leaf(key, value)
        else:
            # 삽입할 위치 찾기
            insertNode = self.find_key_leaf_node(key)
            # print("[디버깅]",  key, "값은 여기에 삽입하면 됨 - keys : ", insertNode.keys)
            insertNode.insert_leaf(key, value)

        # STEP 2 ) leaf node에서 overflow가 나는지 확인 후 overflow가 나는 경우 split
        if(insertNode.get_node_size() < self.degree):
            # leaf node에서 overflow가 나지 않은 경우
            insertNode.save_to_file() # 변경 사항 파일에 저장 후 종료
            return
        else:
            # leaf node에서 overflow가 나는 경우 split
            # print("[디버깅]", key,  "값 삽입 도중 leaf node에서 overflow가 발생했습니다.")
            newSplitNode = insertNode.split_leaf_node()

            if(insertNode == self.root): # root node에서 split이 발생하는 경우
                newSplitNode.write_to_file() # 새로 만들어진 Node의 offset을 구하기 위해 우선 file에 써줌

                # 새로운 root node를 만들어 두개의 split된 노드를 child node로 넣어주기
                newRoot = Node(self.degree)
                # 새로운 root node의 offset을 구하기 위해 우선 file에 써줌
                newRoot.write_to_file()

                newRoot.insert_child_node(insertNode)
                newRoot.insert_child_node(newSplitNode)
                self.root = newRoot

                # 변경 사항들을 다시 file에 저장
                newRoot.save_to_file()
                insertNode.save_to_file()
                newSplitNode.save_to_file()
                
                # root node의 child node가 2개뿐이므로 overflow 판단 할 필요 없이 종료
                return
                
            else:
                newSplitNode.write_to_file() # split되어 새로 생성된 node의 offset을 구하기 위해 우선 file에 씀
                insertNode.save_to_file()    # split된 node 변경 사항 file에 저장 (newSplitNode의 offset이 정해진 후에 insertNode file에 저장)

                # 부모 노드에 split되어 새로 만들어진 node를 child node로 추가
                insertNode = insertNode.get_parent_node()
                insertNode.insert_child_node(newSplitNode)
                

                # 부모 노드가 최소 사이즈 조건을 만족하는 경우
                # 부모 노드의 변경 사항도 저장하고 종료
                if(insertNode.get_node_size() < self.degree):
                    insertNode.save_to_file()
                    return
                
            
        # STEP 3 ) parent node에서 overflow가 나는 경우 -> parent node를 split
        # overflow가 일어나지 않을 때 까지 위로 올라가며 해당 과정 반복
        while(insertNode and insertNode.get_node_size() > self.degree-1):
            #print(f"[디버깅] {key} 값 삽입 도중 non-leaf node( keys : {insertNode.keys} values : {insertNode.pointers})에서 overflow가 발생했습니다.")

            # split
            newSplitNode = insertNode.split_non_leaf_node()
            
            # split하고자 하는 node가 root node인 경우
            if insertNode.offset == self.root.offset:

                newRoot = Node(self.degree) # 새로운 root node만들기
                newRoot.isLeaf = False
                newRoot.write_to_file() # offset을 얻기 위해 일단 저장

                # newSplitNode.save_to_file() # offset을 얻기 위해 일단 저장

                newRoot.keys.append(newSplitNode.get_subtree_smallest_key())
                newRoot.pointers.append(insertNode.offset)
                newRoot.pointers.append(newSplitNode.offset)
                insertNode.parent = newRoot.offset
                newSplitNode.parent = newRoot.offset
                self.root = newRoot

                # 변경 사항 file에 저장
                newRoot.save_to_file()
                insertNode.save_to_file()
                newSplitNode.save_to_file()

                return
            else:
                # split된 node 변경 사항 file에 저장
                # newSplitNode.save_to_file() # insertNode의 next 저장을 위해 우선 file에 저장
                insertNode.save_to_file()

                insertNode = insertNode.get_parent_node()
                insertNode.insert_child_node(newSplitNode)

                # split되어 새로 생성된 node file에 저장
                newSplitNode.save_to_file()
                insertNode.save_to_file() # child node가 1개 추가되었으므로 수정 사항 file에 저장

    #----------------------------------------- DELETE ---------------------------------------#

    def delete (self, key):

        # STEP 1-1 ) leaf node에서 값 삭제하기 

        # 해당 key값이 존재하는 leaf node 찾기
        leafNode = self.find_key_leaf_node(key)
        
        # leaf node에서 값 삭제
        if(leafNode.delete_leaf_node(key) == False): # key 값이 존재하지 않는 경우
            return False


        # STEP 1-2 ) non-leaf node에 해당 key 값이 존재하는 경우 조정

        # leaf node를 제외한 node에 해당 key 값이 존재하는 경우 해당 key 값을 적절한 key 값으로 변경
        if( key < leafNode.keys[0]):
            self.arrange_key(leafNode)

        # leaf node가 최소 사이즈 조건을 만족 하는 경우 변경 사항 file에 저장 후 함수 종료
        if(leafNode.get_node_size() >= minimum_key_number(self.degree)):
            leafNode.save_to_file()
            return True
        

        # STEP 3 ) leaf node가 underflow가 나는 경우 형제 노드로 부터 데이터 1개 가져오기

        # leaf node가 최소 key 사이즈 조건을 만족하지 못하는 경우
        # parent node에서의 위치 찾기
        leafNode_index = 0
        parentNode = Node(self.degree)
        parentNode.load_from_file(leafNode.parent)
        #print(f"[디버깅] leafNode offset : {leafNode.offset}, parent node offset : {parentNode.offset}")
        for i in range (len(parentNode.pointers)):
            if(leafNode.offset == parentNode.pointers[i]):
                leafNode_index = i
                #print(f"[디버깅] 현재 노드의 index는 {i} 입니다. (parent node keys : {parentNode.keys})")
                break
        
        # 오른쪽 형제 노드의 사이즈 체크
        if(leafNode_index < len(parentNode.pointers)-1): # 오른쪽 형제 노드가 존재하는 경우
            # 오른쪽 노드 객체화 (file에서 정보 가져옴)
            rightSibling = Node(self.degree)
            rightSibling.load_from_file(parentNode.pointers[leafNode_index+1])
            if(rightSibling.get_node_size() > minimum_key_number(self.degree)): # 오른쪽 형제 노드에서 데이터를 1개 가져와도 오른쪽 노드가 최소 사이즈 조건을 만족하는 경우
                # 오른쪽 형제 노드로부터 값을 1개 가져올 수 있는 경우
                # print("[디버깅] leaf node의 key 값이 부족합니다. 오른쪽 형제 노드에서 가져옵니다.")
                moveKey = rightSibling.delete_key(0)
                moveValue = rightSibling.delete_pointer(0)
                leafNode.insert_leaf(moveKey, moveValue)
                parentNode.keys[leafNode_index] = rightSibling.keys[0] # 부모 노드의 key 값 조정

                # 변경값 file에 저장
                leafNode.save_to_file()
                rightSibling.save_to_file()
                parentNode.save_to_file()
                return True
        
        # 오른쪽 형제노드에셔 빌려올 수 없는 경우
        # 왼쪽 형제 노드의 사이즈 체크
        if(leafNode_index > 0): # 왼쪽 형제 노드가 존재하는 경우
            # 왼쪽 형제 노드 객체화 (file로부터 정보 읽어옴)
            leftSibling = Node(self.degree)
            leftSibling.load_from_file(parentNode.pointers[leafNode_index-1])
            if(leftSibling.get_node_size() > minimum_key_number(self.degree)): # 왼쪽 형제노드로부터 데이터를 1개 가져올 수 있는 경우
                # print("[디버깅] leaf node의 key 값이 부족합니다. 왼쪽 형제 노드에서 가져옵니다.")
                key = leftSibling.delete_key(leftSibling.get_node_size()-1)
                value = leftSibling.delete_pointer(leftSibling.get_node_size()) # 값이 이미 삭제된 후 이므로 key와 동일한 Index의 pointer를 가져오기 위해서는 get_node_size()를 써야함
                leafNode.insert_leaf(key, value)
                parentNode.keys[leafNode_index-1] = key

                # 변경 사항 file에 저장
                leafNode.save_to_file()
                leftSibling.save_to_file()
                parentNode.save_to_file()
                return True


        # STEP 3 ) 형제 노드로 부터 데이터를 가져올 수 없는 경우 형제 노드와 merge

        # 양쪽 형제노드에서 빌려올 수 없는 경우
        # 오른쪽 형제가 존재할 경우 오른쪽 형제 노드와 합치기
        if(leafNode_index < len(parentNode.pointers)-1):
            # 오른쪽 형제 노드 객체화
            rightSibling = Node(self.degree)
            rightSibling.load_from_file(parentNode.pointers[leafNode_index+1])

            # print(f"[디버깅] leaf node의 key 값이 부족합니다. 오른쪽 형제 노드와 merge 합니다. (오른쪽 형제노드의 keys : {rightSibling.keys})")
            leafNode.merge_leaf_node(rightSibling)
            leafNode.next = rightSibling.next
            leafNode.save_to_file() # 변경 사항 저장 (merge)

            parentNode.delete_key(leafNode_index)
            parentNode.delete_pointer(leafNode_index+1)
            parentNode.save_to_file()
            # [추가 필요] 오른쪽 노드 file에서 삭제

        elif(leafNode_index > 0):
            # 오른쪽 형제 노드가 존재하지 않는 경우 왼쪽 형제 노드와 합치기

            # 왼쪽 형제 노드 객체화
            leftSibling = Node(self.degree)
            leftSibling.load_from_file(parentNode.pointers[leafNode_index-1])
            # print(f"[디버깅] leaf node의 key 값이 부족합니다. 왼쪽 형제 노드와 merge 합니다. (왼쪽 형제노드의 keys : {leftSibling.keys})")
            
            leftSibling.merge_leaf_node(leafNode)
            # [추가 필요] leafNode file에서 삭제
            leftSibling.next = leafNode.next
            leftSibling.save_to_file() # 변경 사항 저장 (merge)

            parentNode.delete_key(leafNode_index-1)
            parentNode.delete_pointer(leafNode_index)
            parentNode.save_to_file()
        if(len(parentNode.pointers) == 1):
            # 현재 노드를 root node로 두고 종료 [확인 필요]
            # print("[디버깅] 형재 노드가 존재하지 않습니다. 현재 노드를 root node로 설정합니다")
            leafNode.parent = None
            leafNode.save_to_file()
            self.root = leafNode
            self.write_bptree_to_file()
            self.load_bptree_from_file()
            rootOffset = self.root
            self.root = Node(self.degree)
            self.root.load_from_file(rootOffset)
            #print(f"[디버깅] root offset :{self.root.offset} root keys : {self.root.keys} root pointers : {self.root.pointers}")
            return True

        # 부모 노드의 key 값이 1 감소했으므로 사이즈 체크 필요       
        if(parentNode.get_node_size() >= minimum_key_number(self.degree)):
            # 부모 노드가 최소 조건을 만족하는 경우
            # 부모 노드의 변경 사항 저장 후 종료
            parentNode.save_to_file()
            return True



        # STEP 5 ) 부모노드 부터 위로 올라가며 최소 조건을 만족하지 못하는 경우 형제 노드로부터 가져오거나 형제 노드와 합치기

        # key 값이 부족한 경우 형재 노드로부터 가져오거나 형제 노드와 merge
        # merge시 부모 노드 사이즈 체크
        nodePointer = parentNode
        while(nodePointer.get_node_size() < minimum_key_number(self.degree) and nodePointer.parent != None):
            #print(f"[디버깅] 현재 노드 정보 - offset : {nodePointer.offset} , keys : {nodePointer.keys} , pointers : {nodePointer.pointers}")
            # 부모 노드에셔의 위치 (index) 찾기
            index = 0
            parentNode = Node(0)
            parentNode.load_from_file(nodePointer.parent)
            for i in range (len(parentNode.pointers)):
                if(nodePointer.offset == parentNode.pointers[i]):
                    index = i
                    # print("[디버깅] 현재 node의 index는", index, "입니다.")
                    break

            # 가능한 경우 오른쪽 형제노드로부터 child node를 1개 가져옴
            if(index < len(parentNode.pointers)-1): # 오른쪽 형제노드가 존재하는 경우
                rightSibling = Node(self.degree)
                rightSibling.load_from_file(parentNode.pointers[index+1])
                if(rightSibling.get_node_size() > minimum_key_number(self.degree)): #오른쪽 형제노드로부터 가져올 수 있는 경우
                    # print("[디버깅] 오른쪽 형제노드로부터 child node를 1개 가져옵니다.")
                    #print(f"[디버깅] parent node offset : {parentNode.offset} parent node keys : {parentNode.keys} , parent node pointers : {parentNode.pointers}")
                    #print(f"[디버깅] right sibling offset : {rightSibling.offset}, right sibling keys : {rightSibling.keys}")
                    nodePointer.insert_child_node(rightSibling.pointers[0]) #오른쪽 형제 노드의 가장 왼쪽 child node가져옴
                    rightSibling.delete_pointer(0)
                    rightSibling.delete_key(0)

                    rightSibling.save_to_file()
                    nodePointer.save_to_file()

                    self.arrange_key(rightSibling)

                    # 부모 노드의 사이즈가 변경되지 않았으므로 종료
                    return True

            # 가능한 경우 왼쪽 형제노드로부터 child node를 1개 가져옴
            if(index > 0): # 왼쪽 형제 노드가 존재하는 경우
                leftSibling = Node(self.degree)
                leftSibling.load_from_file(parentNode.pointers[index-1])
                if( leftSibling.get_node_size() < minimum_key_number(self.degree)): # 왼쪽 노드로부터 값을 가져올 수 있는 경우
                    # print("[디버깅] 왼쪽 형제노드로부터 child node를 1개 가져옵니다.")
                    #print(f"[디버깅] parent node offset : {parentNode.offset} parent node keys : {parentNode.keys} , parent node pointers : {parentNode.pointers}")
                    #print(f"[디버깅] left sibling offset : {leftSibling.offset}, left sibling keys : {leftSibling.keys}")
                    
                    nodePointer.insert_child_node(rightSibling.pointers[len(rightSibling.pointers)-1])
                    leftSibling.delete_pointer[len(leftSibling.pointers)-1]
                    leftSibling.delete_key[len(leftSibling.keys)-1]
                    
                    nodePointer.save_to_file()
                    leftSibling.save_to_file()

                    self.arrange_key(nodePointer)
                    return True

            # 형제 노드로부터 child node를 가져올 수 없는 경우
            # 오른쪽 노드와 합치기
            if(index < len(parentNode.pointers)-1):
                # print("[디버깅] 오른쪽 형제노드와 merge합니다.")
                rightSibling = Node(self.degree)
                rightSibling.load_from_file(parentNode.pointers[index+1])

                nodePointer.merge_non_leaf_node(rightSibling)

                parentNode.delete_key(index)
                parentNode.delete_pointer(index+1)
                # [추가 필요] 오른쪽 노드 삭제
                nodePointer.save_to_file() # 변경 사항 저장 (merge)
                parentNode.save_to_file()
            elif(index > 0):
                # print("[디버깅] 왼쪽 형제노드와 merge합니다.")
                leftSibling = Node(self.degree)
                leftSibling.load_from_file(parentNode.pointers[index-1])

                nodePointer.merge_non_leaf_node(leftSibling)

                # [추가 필요] 왼쪽 노드 삭제
                parentNode.delete_key(index-1)
                parentNode.delete_pointer(index-1)

                nodePointer.save_to_file() # 변경 사항 저장 (merge)
                parentNode.save_to_file()
            if(len(parentNode.pointers) == 1):
                # 형제 노드가 존재하지 않는 경우
                # 현재 노드를 root node로 지정 후 종료 (확인 필요)
                # print("[디버깅] sibling node가 존재하지 않습니다. 현재 node를 root node로 변경합니다")
                nodePointer.parent = None
                nodePointer.save_to_file()
                self.root = nodePointer
                self.write_bptree_to_file()
                self.load_bptree_from_file()
                rootOffset = self.root
                self.root = Node(self.degree)
                self.root.load_from_file(rootOffset)
                # print(f"[디버깅] root offset :{self.root.offset} root keys : {self.root.keys} root pointers : {self.root.pointers}")
                return True


            nodePointer.load_from_file(nodePointer.parent)

        nodePointer.save_to_file()


    # modifiedNode(leaf node)의 첫번째 key값이 변화한 경우 상단 node들의 key 값을 조정해주는 함수    
    def arrange_key (self, modifiedNode):
        nodePointer = modifiedNode
        newKey = modifiedNode.get_subtree_smallest_key()

        while(nodePointer.parent != None):
            parentNode = Node(self.degree)
            parentNode.load_from_file(nodePointer.parent)

            if(nodePointer.offset == parentNode.pointers[0]):
                nodePointer = parentNode
                continue
            
            for i in range(len(parentNode.pointers)):
                if(nodePointer.offset == parentNode.pointers[i] and i > 0):
                    #print("[디버깅] 상단의 key 값을 변경합니다. (" , parentNode.keys[i-1] , "->", newKey, ")")
                    parentNode.keys[i-1] = newKey
                    parentNode.save_to_file() # key 값 변경 시 변경 사항 file에 저장
                    return
            return


    #------------------------------------------ DEBUG ----------------------------------------#


def main():
    global IndexFile
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--create", nargs=2, metavar=("index_file", "node_size"))
    parser.add_argument("-i", "--insert", nargs=2, metavar=("index_file", "data_file"))
    parser.add_argument("-d", "--delete", nargs=2, metavar=("index_file", "data_file"))
    parser.add_argument("-s", "--search", nargs=2, metavar=("index_file", "key"))
    parser.add_argument("-r", "--range_search", nargs=3 , metavar=("index_file", "start_key", "end_key"))

    args = parser.parse_args()
    #print(args)

    if args.create:
        index_file, node_size = args.create

        with open(index_file, 'wb') as indexFile:
            IndexFile= indexFile
            bptree = BplusTree(int(node_size)) # 트리 객체 생성
            bptree.root = 512
            bptree.write_bptree_to_file() # 트리 file에 저장
            bptree.root = Node(int(node_size)) # root node 객체 생성
            bptree.root.write_to_file_with_offset(512) # root node file에 저장

    elif args.insert:
        index_file, data_file = args.insert
        # print("[디버깅] insert를 실행합니다.", index_file, data_file)

        with open(index_file, 'rb+') as indexFile:
            IndexFile = indexFile
            # b+ tree 정보 읽어와 객체 생성하기
            IndexFile.seek(0)
            bptree = BplusTree(0)
            bptree.load_bptree_from_file()
            # print(f"[디버깅] bptree 정보 ) bptee.degree :{bptree.degree}, bptree.nodeOffset : {bptree.nodeOffset}, bptree.root {bptree.root}")
            
            # root node 정보 읽어와 객체 생성하기
            rootOffset = bptree.root
            bptree.root = Node(bptree.degree)
            bptree.root.load_from_file(rootOffset)
            # print(f"[디버깅] bptree.root 정보 ) degree : {bptree.root.degree},  offset : {bptree.root.offset}, keys : {bptree.root.keys} , pointers: {bptree.root.pointers}, isLeaf : {bptree.root.isLeaf}\n")


            # print("[디버깅] Insert를 시작합니다\n")
            with open(data_file,mode='r', newline="") as dataFile:
                csv_reader = csv.reader(dataFile)

                for row in csv_reader:
                    #print(f"\n\n===== [디버깅] {int(row[0])}, {int(row[1])}을 삽입합니다 =====")
                    bptree.root.load_from_file(bptree.root.offset) # 이전 insert에서 root가 변경되었을 수 있기 때문에 다시 file로부터 불러옴
                    bptree.insert(int(row[0]) , int(row[1]))
            
            # b+ tree관련 변경사항이 있을 경우 (root 변경) 변경 사항 file에 저장
            bptree.root = bptree.root.offset
            bptree.write_bptree_to_file()


    elif args.delete:
        index_file, data_file = args.delete
        # print("[디버깅] delet를 실행합니다.", index_file, data_file)

        with open (index_file, "rb+") as indexFile:
            IndexFile = indexFile
            bptree = BplusTree(0)
            bptree.load_bptree_from_file()

            rootOffset = bptree.root
            bptree.root = Node(bptree.degree)
            bptree.root.load_from_file(rootOffset)

            with open(data_file, mode="r" , newline="") as dataFile:
                csv_reader = csv.reader(dataFile)

                for row in csv_reader:
                    # print(f"\n\n===== [디버깅] {int(row[0])}을 삭제합니다 =====")
                    bptree.root.load_from_file(bptree.root.offset)
                    bptree.delete(int(row[0]))
            # print(f"[디버깅] root : {bptree.root.offset} root keys : {bptree.root.keys} root pointers : {bptree.root.pointers}")
            bptree.write_bptree_to_file()

    elif args.search:
        index_file, key = args.search
        # print("[디버깅] search를 실행합니다.", index_file, key)

        with open(index_file, 'rb') as indexFile:
            IndexFile = indexFile
            
            # b+ tree 정보 file로부터 읽어오기
            bptree = BplusTree(0)
            bptree.load_bptree_from_file()

            # root node 정보 file로부터 load해 객체화 하기
            rootOffset = bptree.root
            bptree.root = Node(bptree.degree)
            bptree.root.load_from_file(rootOffset)

            bptree.single_search(int(key))


    elif args.range_search:
        index_file, start_key, end_key = args.range_search
        # print("[디버깅] range_search를 실행합니다.", index_file, start_key, end_key)

        with open(index_file, 'rb') as indexFile:
            IndexFile = indexFile
            
            # b+ tree 정보 file로부터 읽어오기
            bptree = BplusTree(0)
            bptree.load_bptree_from_file()

            # root node 정보 file로부터 load해 객체화 하기
            rootOffset = bptree.root
            bptree.root = Node(bptree.degree)
            bptree.root.load_from_file(rootOffset)

            bptree.range_search(int(start_key), int(end_key))


if __name__ == "__main__":
    main()