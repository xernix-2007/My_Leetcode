class Solution {
public:
    long long mergeSort(vector<long long>& a, int l, int r, int diff) {
        if(l >= r) return 0;
        int mid = l + (r - l) / 2;
        long long count = 0;
        count += mergeSort(a, l, mid, diff);
        count += mergeSort(a, mid + 1, r, diff);
        // Count pairs: i in left, j in right
        int j = mid + 1;
        for(int i = l; i <= mid; i++) {
            while(j <= r && a[i] > a[j] + diff)
                j++;
            count += r - j + 1;
        }
        // Normal merge
        vector<long long> temp;
        int i = l;
        j = mid + 1;
        while(i <= mid && j <= r) {
            if(a[i] <= a[j])
                temp.push_back(a[i++]);
            else
                temp.push_back(a[j++]);
        }
        while(i <= mid)
            temp.push_back(a[i++]);
        while(j <= r)
            temp.push_back(a[j++]);
        for(int k = l; k <= r; k++)
            a[k] = temp[k - l];
        return count;
    }
    long long numberOfPairs(vector<int>& nums1,vector<int>& nums2,int diff) {
        int n = nums1.size();
        vector<long long> a(n);
        for(int i = 0; i < n; i++)
            a[i] = (long long)nums1[i] - nums2[i];
        return mergeSort(a, 0, n - 1, diff);
    }
};