import React, { useState } from 'react'
import Select from 'react-select'

const transformVendors = function (vendorDetail) {
    // Use an object to store unique vendors
    const uniqueVendors = {};

    // Iterate over the data to filter unique vendors
    vendorDetail.forEach(v => {
        if (!uniqueVendors[v.vendor]) {
            uniqueVendors[v.vendor] = {
                value: v.vendor,
                label: v.vendor,
                account_id: v.account_id,
            };
        }
    });

    // Convert the unique vendors object back to an array
    return Object.values(uniqueVendors);
};

const transformAccounts = (vendorDetail, selectedVendor) => {
    // Filter the vendor detail based on the selected vendor and transform to account_id options
    return vendorDetail
        .filter((v) => v.vendor === selectedVendor) // Filter only the selected vendor
        .map((v) => ({
            value: v.account_id,
            label: v.account_id,
        }));
};

const transformResponseData = (responseData) => {
    return responseData.map((item) => ({
      value: item.name,
      label: item.name,
    }));
};

const SyncTemplate = ({ vendorDetail }) => {
    const [selectedVendor, setSelectedVendor] = useState(null);
    const [viewAccountIdOption, setViewAccountIdOption] = useState(false);

    const handleVendorChange = (selectedOption) => {
        setSelectedVendor(selectedOption.value); // Store the selected vendor
        setViewAccountIdOption(true); // Show the second Select component
        setViewThirdOption(false); // Reset third dropdown visibility
        setThirdDropdownOptions([]); // Clear third dropdown options
    };
    return (
        <>
            <Select
                options={transformVendors(vendorDetail)} // Vendor options
                onChange={handleVendorChange} // Handle selection change
            />
            {viewAccountIdOption && (
                <Select
                    options={transformAccounts(vendorDetail, selectedVendor)} // Account options for the selected vendor
                    onChange={handleAccountChange}
                />
            )}
            {viewThirdOption && (
                <Select
                    options={thirdDropdownOptions}
                />
            )}
        </>
    );
}

const handleAccountChange = async (selectedOption) => {
    setSelectedAccountId(selectedOption.value);
    // Call API to fetch data based on selected account_id
    try {
      const response = await axios.get(`?account_id=${selectedOption.value}`);
      const options = transformResponseData(response.data.data);
      setThirdDropdownOptions(options); // Set options for the third dropdown
      setViewThirdOption(true); // Show the third dropdown
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

export default SyncTemplate;
