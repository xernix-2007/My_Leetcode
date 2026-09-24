class Solution {
public:
    int longestSubarray(vector<int>& nums, int limit) {
        deque<int> maxi;
        deque<int> mini;
        int l = 0;
        int ans = 0;
        for (int r = 0; r < nums.size(); r++) {
            // Maintain decreasing deque for maximum
            while (!maxi.empty() && nums[maxi.back()] < nums[r]) {
                maxi.pop_back();
            }
            maxi.push_back(r);
            // Maintain increasing deque for minimum
            while (!mini.empty() && nums[mini.back()] > nums[r]) {
                mini.pop_back();
            }
            mini.push_back(r);
            // Window invalid
            while (nums[maxi.front()] - nums[mini.front()] > limit) {
                if (maxi.front() == l)
                    maxi.pop_front();
                if (mini.front() == l)
                    mini.pop_front();
                l++;
            }
            ans = max(ans, r - l + 1);
        }
        return ans;
    }
};