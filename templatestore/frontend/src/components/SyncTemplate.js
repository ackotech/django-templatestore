import React, { useState, useEffect } from "react";
import Select from "react-select";
import axios from "axios";
import { FidgetSpinner } from "react-loader-spinner";
import { backendSettings } from "./../utils.js";

const transformVendors = vendorDetail => {
  if (!vendorDetail) return [];
  const uniqueVendors = {};
  vendorDetail.forEach(v => {
    if (!uniqueVendors[v.vendor]) {
      uniqueVendors[v.vendor] = {
        value: v.vendor,
        label: v.vendor,
        account_id: v.account_id
      };
    }
  });
  return Object.values(uniqueVendors);
};

const transformAccounts = (vendorDetail, selectedVendor) => {
  return vendorDetail
    .filter(v => v.vendor === selectedVendor)
    .map(v => ({
      value: v.account_id,
      label: v.account_id
    }));
};

const transformResponseData = responseData => {
  return responseData.map(item => ({
    value: item.name,
    label: item.name
  }));
};

const SyncTemplate = ({ stateVar }) => {
  const [selectedAccountId, setSelectedAccountId] = useState(null);
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [viewAccountIdOption, setViewAccountIdOption] = useState(false);
  const [thirdDropdownOptions, setThirdDropdownOptions] = useState([]);
  const [viewThirdOption, setViewThirdOption] = useState(false);
  const [loader, setLoader] = useState(false);

  // Ensure vendor details are available
  if (!stateVar.vendorDetail) return null;

  // Handle vendor change
  const handleVendorChange = selectedOption => {
    setSelectedVendor(selectedOption);
    setViewAccountIdOption(true);
    setViewThirdOption(false);
    setThirdDropdownOptions([]);
  };

  // Handle account change
  const handleAccountChange = selectedOption => {
    setSelectedAccountId(selectedOption);
  };

  // API call using useEffect based on accountId and vendor selection
  useEffect(() => {
    if (selectedAccountId && selectedVendor && stateVar.type) {
      setLoader(true);
      axios
        .get(
          `${backendSettings.TE_BASEPATH}/internal/api/v1/vendor/${selectedVendor.value}/channel/${stateVar.type}/?account_id=${selectedAccountId.value}`
        )
        .then(response => {
          const options = transformResponseData(response.data.data);
          console.log("setThirdDropdownOptions ", options);
          setThirdDropdownOptions(options);
          setViewThirdOption(true);
          setLoader(false);
        })
        .catch(error => {
          console.error("Error fetching data:", error);
          setLoader(false);
        });
    }
  }, [selectedAccountId, selectedVendor, stateVar.type]); // Dependency array for useEffect

  return (
    <>
      {loader ? (
        <FidgetSpinner />
      ) : (
        <>
          <Select
            value={selectedVendor}
            options={transformVendors(stateVar.vendorDetail.data)}
            onChange={handleVendorChange}
          />
          {viewAccountIdOption && (
            <Select
              value={selectedAccountId}
              options={transformAccounts(
                stateVar.vendorDetail.data,
                selectedVendor?.value
              )}
              onChange={handleAccountChange}
            />
          )}
          {viewThirdOption && <Select options={thirdDropdownOptions} />}
        </>
      )}
    </>
  );
};

export default SyncTemplate;
