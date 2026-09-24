class Solution {
public:
    long long gcdSum(vector<int>& nums) {
        vector<int> g;
        int m=0;
        int a=0;
        for(int i=0;i< nums.size();i++){
            m=max(m,nums[i]);
            a=gcd(nums[i],m);
            g.push_back(a);
        }
        long long sum=0;
        int b=0;
        sort(g.begin(),g.end());
        for(int i=0;i<g.size()/2;i++){
            b=gcd(g[i],g[g.size()-1-i]);
            sum+=b;
        }
        return sum;
    }
};