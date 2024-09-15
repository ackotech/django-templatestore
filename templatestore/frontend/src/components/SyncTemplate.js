import React, { useState, useEffect } from "react";
import Select from "react-select";
import axios from "axios";
import { FidgetSpinner } from "react-loader-spinner";
import { backendSettings } from "./../utils.js";
import styles from '../style/WhatsAppEditor.less';
import { withRouter } from "react-router-dom";

const transformVendors = (vendorDetail, channel) => {
  if (!vendorDetail) return [];
  const uniqueVendors = {};
  vendorDetail.forEach(v => {
    if (!uniqueVendors[v.vendor] && v.channel.toLowerCase() == channel.toLowerCase()) {
      uniqueVendors[v.vendor] = {
        value: v.vendor,
        label: v.vendor,
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

const accountIdMap = {
  "2000184968": "Acko UAT One Way (Most common)",
  "2000184969": "Acko UAT Two Way",
  "2000214144": "Acko Tech (Electronics)",
  "2000231746": "Acko Life",
  "2000238490": "Auto Garage",
  "2000189615": "Acko Drive",
  "2000184970": "Acko PROD One Way (Most common)",
  "2000184971": "Acko PRDO Two Way",
  "1101556610000021991": "Only Account"
}

const transformAccounts = (vendorDetail, selectedVendor) => {
  return vendorDetail
    .filter(v => v.vendor === selectedVendor)
    .map(v => ({
      value: v.account_id,
      label: v.account_id + " " + accountIdMap[v.account_id]
    }));
};

const transformResponseData = responseData => {
  return responseData.filter(item => item['status'].toLowerCase() === 'enabled').map(item => ({
    value: item.name,
    label: item.name
  }));
};

const transformSmsData = reponseData => {
  return reponseData['templates'].map(item => ({
    value: item['tname'],
    label: item['tname']
  }));
};

const SyncTemplate = ({ stateVar, history }) => {
  const [selectedChannel, setSelectedChannel] = useState(stateVar.type);
  const [selectedAccountId, setSelectedAccountId] = useState(null);
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [viewAccountIdOption, setViewAccountIdOption] = useState(false);
  const [thirdDropdownOptions, setThirdDropdownOptions] = useState([]);
  const [viewThirdOption, setViewThirdOption] = useState(false);
  const [viewMesageSenderOption, setViewMesageSenderOption] = useState(false);
  const [selectedTemplateName, setSelectedTemplateName] = useState(null);
  const [selectedMessageSender, setSelectedMesageSender] = useState(null);

  const [viewMesageSenderAccountIdOption, setViewMesageSenderAccountIdOption] = useState(false);
  const [messageSenderAccountIdDropdownOptions, setMessageSenderAccountIdDropdownOptions] = useState([]);
  const [selectedMessageSenderAccountId, setSelectedMessageSenderAccountId] = useState(null);

  const [messageSenderDropdownOptions, setMessageSenderDropdownOptions] = useState([]);
  const [loader, setLoader] = useState(false);
  const [viewButton, setViewButton] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Ensure vendor details are available
  if (!stateVar.vendorDetail) return null;

  // Handle vendor change
  const handleVendorChange = selectedOption => {
    setSelectedVendor(selectedOption);
    setViewAccountIdOption(true);
    setViewThirdOption(false);
    setThirdDropdownOptions([]);
    setViewMesageSenderOption(false);
    setSelectedAccountId('');
    setSelectedTemplateName('');
    setIsSubmitting(false);
  };

  // Handle account change
  const handleAccountChange = selectedOption => {
    setSelectedAccountId(selectedOption);
    setSelectedTemplateName('');
  };

  const messageSenderOptionFn = () => {
    let vendorDetails = stateVar.vendorDetail.data
    if (!vendorDetails) return [];
    let smsDetails = [];
    vendorDetails.forEach(v => {
      if (v.vendor.toLowerCase() === selectedVendor.value.toLowerCase() && v.channel.toLowerCase() == stateVar.type.toLowerCase()) {
        smsDetails = v.metadata.sender_details
      }
    });
    
    let senderAccountProvider = new Set();
    smsDetails.forEach(item => {
      senderAccountProvider.add(item.dlt_message_sender)
    })
    setMessageSenderDropdownOptions(Array.from(senderAccountProvider).map(item => ({
      "label": item,
      "value": item
    })));
  }

  const messageSenderAccountIdOptionsFn = (selectedOption) => {
    let vendorDetails = stateVar.vendorDetail.data
    if (!vendorDetails) return [];
    let smsDetails = [];
    vendorDetails.forEach(v => {
      if (v.vendor.toLowerCase() === selectedVendor.value.toLowerCase() && v.channel.toLowerCase() == stateVar.type.toLowerCase()) {
        smsDetails = v.metadata.sender_details
      }
    });

    setMessageSenderAccountIdDropdownOptions(smsDetails.filter(item => item.dlt_message_sender === selectedOption.value).map(item => ({
      "label": item.id + " " + item.message_sender_account_id,
      "value": item.message_sender_account_id
    })));
  }

  const handleTemplateChange = selectedOption => {
    setSelectedTemplateName(selectedOption)
    if (stateVar.type == 'whatsapp') {
      setViewButton(true);
    }
    if (stateVar.type == 'sms') {
      messageSenderOptionFn();
      setViewMesageSenderOption(true);
    }
  }

  const handleMessageSenderChange = selectedOption => {
    setSelectedMesageSender(selectedOption);
    if (stateVar.type == 'sms') {
      setViewMesageSenderAccountIdOption(true);
      messageSenderAccountIdOptionsFn(selectedOption);
    }
  }

  const handleMessageSenderAccountIdChange = selectedOption => {
    setSelectedMessageSenderAccountId(selectedOption);
    setViewButton(true);
  }

  const postSyncTemplate = () => {
    setIsSubmitting(true);
    setLoader(true);
    let req = {}
    if (stateVar.type.toLowerCase() === 'whatsapp') {
      req = {
          account_id: String(selectedAccountId.value),
          name: String(selectedTemplateName.value)
      }
    }
    else if (stateVar.type.toLowerCase() === 'sms') {
        req = {
          account_id: String(selectedAccountId.value),
          name: String(selectedTemplateName.value),
          dlt_message_sender: selectedMessageSender.value,
          message_sender_account_id: selectedMessageSenderAccountId.value
      }
    }
    axios.post(
        `${backendSettings.TE_BASEPATH}/api/v1/template/${selectedVendor.value.toLowerCase()}/channel/${stateVar.type}/sync`,
        req
    )
    .then(response => {
        setIsSubmitting(false);
        setLoader(false);
        // TODO: Check this 
        history.push(
            backendSettings.TE_BASEPATH +
                '/t/' +
                response.data.name +
                '/' +
                response.data.version
        );
    })
    .catch(error => {
        console.error("Error saving auto fetch -> ", error);
        setIsSubmitting(false);
        setLoader(false);
    });
  }

  // API call using useEffect based on accountId and vendor selection
  useEffect(() => {
    if (selectedChannel !== stateVar.type) {
      setSelectedVendor('');
      setSelectedAccountId('');
      setSelectedTemplateName("");
      setSelectedMesageSender('');
      setSelectedMessageSenderAccountId('');
      setViewAccountIdOption(false);
      setViewThirdOption(false);
      setViewMesageSenderOption(false);
      setViewMesageSenderAccountIdOption(false);
      setSelectedChannel(stateVar.type);
    }
    else if (selectedAccountId && selectedVendor && stateVar.type) {
      setLoader(true);
      axios
        .get(
          `${backendSettings.TE_BASEPATH}/internal/api/v1/vendor/${selectedVendor.value}/channel/${stateVar.type}/?account_id=${selectedAccountId.value}`
        )
        .then(response => {
          let options;
          if (stateVar.type.toLowerCase() == "whatsapp") {
            options = transformResponseData(response.data.data);
          }
          else if (stateVar.type.toLowerCase() == "sms") {
            options = transformSmsData(response.data);
          }
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
            options={transformVendors(stateVar.vendorDetail.data, stateVar.type)}
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
          
          
          {viewMesageSenderOption && (
            <Select options={messageSenderDropdownOptions} 
                    value={selectedMessageSender} 
                    placeholder="Select the Message Sender Provider"
                    onChange={handleMessageSenderChange}
                    styles={customStyles} />)}
          
          {viewMesageSenderAccountIdOption && (
            <Select options={messageSenderAccountIdDropdownOptions} 
                    value={selectedMessageSenderAccountId} 
                    placeholder="Select the Message Sender Account Id"
                    onChange={handleMessageSenderAccountIdChange}
                    styles={customStyles} />)}
          
          
          {viewButton && 
          <button className={styles.waButton} 
                  onClick={postSyncTemplate}
                  disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Save Template"}
          </button>
          }
        </>
      )}
    </>
  );
};

export default withRouter(SyncTemplate);
