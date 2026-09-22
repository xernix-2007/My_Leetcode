class Solution {
public:
    int firstMissingPositive(vector<int>& nums) {
        unordered_set<int> st;
        for(int x:nums){
            st.insert(x);
        }
        for(int i =1;i<=nums.size();i++){
            if(st.find(i)==st.end()){
                return i; 
            }
        }
        return nums.size()+1;
    }
};