import React, { useState, useEffect } from "react";
import Select from "react-select";
import axios from "axios";
import { FidgetSpinner } from "react-loader-spinner";
import { backendSettings } from "./../utils.js";
import styles from '../style/WhatsAppEditor.less';

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

const customStyles = {
    control: (provided, state) => ({
      ...provided,
      borderColor: state.isFocused ? "#4a90e2" : "#ddd",
      boxShadow: state.isFocused ? "0 0 0 1px #4a90e2" : "none",
      "&:hover": {
        borderColor: "#4a90e2"
      },
      marginBottom: "12px",
      width: "600px"
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected ? "#4a90e2" : "#fff",
      color: state.isSelected ? "#fff" : "#333",
      width: "600px",
      "&:hover": {
        backgroundColor: "#e6f0ff",
        color: "#333"
      }
    }),
    menu: (provided) => ({
      ...provided,
      marginTop: "0",
      borderRadius: "8px",
      boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
      width: "600px",
    }),
    placeholder: (provided) => ({
      ...provided,
      color: "#888"
    }),
    singleValue: (provided) => ({
      ...provided,
      color: "#333"
    })
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
  return responseData.filter(item => item['status'].toLowerCase() === 'enabled').map(item => ({
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
  const [selectedTemplateName, setSelectedTemplateName] = useState(null);
  const [loader, setLoader] = useState(false);

  // Ensure vendor details are available
  if (!stateVar.vendorDetail) return null;

  // Handle vendor change
  const handleVendorChange = selectedOption => {
    setSelectedVendor(selectedOption);
    setViewAccountIdOption(true);
    setViewThirdOption(false);
    setThirdDropdownOptions([]);
    setSelectedAccountId('');
    setSelectedTemplateName('');
  };

  // Handle account change
  const handleAccountChange = selectedOption => {
    setSelectedAccountId(selectedOption);
    setSelectedTemplateName('');
  };

  const handleTemplateChange = selectedOption => {
    setSelectedTemplateName(selectedOption)
  }

  const postSyncTemplate = () => {
    axios.post(
        `${backendSettings.TE_BASEPATH}/api/v1/template/${selectedVendor.value.toLowerCase()}/channel/${stateVar.type}/sync`,
        
        {
            account_id: String(selectedAccountId.value),
            name: String(selectedTemplateName.value)
        }
    )
    .then(response => {
        // TODO: Check this 
        this.props.history.push(
            backendSettings.TE_BASEPATH +
                '/t/' +
                response.data.name +
                '/' +
                response.data.version
        );
    })
    .catch(error => {
        console.error("Error saving auto fetch -> ", error);
    });
  }

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
        <FidgetSpinner 
            wrapperStyle={{ 
                display: "flex", 
                justifyContent: "center", 
                alignItems: "center", 
                height: "25vh",
                width: "25vw"
          }}
        />
      ) : (
        <>
          <Select
            styles={customStyles}
            value={selectedVendor}
            placeholder="Select the Template Vendor"
            options={transformVendors(stateVar.vendorDetail.data)}
            onChange={handleVendorChange}
          />
          {viewAccountIdOption && (
            <Select
              styles={customStyles}
              value={selectedAccountId}
              placeholder="Select the Account Id for Vendor"
              options={transformAccounts(
                stateVar.vendorDetail.data,
                selectedVendor?.value
              )}
              onChange={handleAccountChange}
            />
          )}
          {viewThirdOption && (
            <Select options={thirdDropdownOptions} 
                    value={selectedTemplateName} 
                    placeholder="Select the Template Name"
                    onChange={handleTemplateChange}
                    styles={customStyles} />)}
          {selectedTemplateName && <button className={styles.waButton} onClick={postSyncTemplate}>Save Template</button>}
        </>
      )}
    </>
  );
};

export default SyncTemplate;
