class Solution {
public:
    vector<int> maxSlidingWindow(vector<int>& nums, int k) {
        multiset<int> st;
        vector<int> ans;
        int l = 0;
        for (int r = 0; r < nums.size(); r++) {
            // Add current element
            st.insert(nums[r]);
            // Window becomes bigger than k
            if (r - l + 1 > k) {
                st.erase(st.find(nums[l]));
                l++;
            }
            // Window size is k
            if (r - l + 1 == k) {
                ans.push_back(*st.rbegin());
            }
        }
        return ans;
    }
};