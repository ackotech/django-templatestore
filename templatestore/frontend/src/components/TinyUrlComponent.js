import React from 'react';
import styles from '../style/templateScreen.less';
import axios from 'axios';
import { backendSettings } from './../utils.js';
import TinyUrlDropdownComponent from './TinyUrlDropdownComponent';

export default function TinyUrlComponent(props) {
    function addNewDropdown() {
        if (props.items.length) {
            if (props.items[props.items.length - 1].urlKey === "" || props.items[props.items.length - 1].expiry === "") {
                props.showAlerts("Please select valid values first");
                return;
            }
        }
        let newItems = [...props.items, { urlKey: "", expiry: "" }];
        props.updateItems(newItems);
    }

    function removeDropdown(e, givenId) {
        e.preventDefault();
        const newItems = props.items.filter(el => el.urlKey !== givenId);
        let visitedCopy = { ...props.visited };
        visitedCopy[givenId] = 0;
        props.updateItems(newItems);
        props.updateVisited(visitedCopy);
    }

    function handleChange(e, id) {
        e.persist();
        if (e.target.value === "") {
            props.showAlerts("Choose valid Url and expiry");
            return;
        }
        let newItems = [...props.items];
        let visitedCopy = { ...props.visited };
        if (e.target.name === 'urlKey') {
            visitedCopy[e.target.value] = 1;
            if (id !== "") {
                visitedCopy[id] = 0;
            }
            props.updateVisited(visitedCopy);
        }
        let index = newItems.findIndex(item => item.urlKey === id);
        newItems[index][e.target.name] = e.target.value;
        props.updateItems(newItems);
    }


    function valueSelected(e) {
        e.preventDefault();
        let data = {};
        for (let i = 0; i < props.items.length; i++) {
            if (props.items[i].urlKey === "" || props.items[i].expiry === "") {
                props.showAlerts("Can't leave url or expiry blank");
                return;
            }
        }
        data.tinyUrlArray = props.items;
        data.templateName = props.templateName ? props.templateName : "";
        data.templateVersion = props.templateVersion ? props.templateVersion : "";
        axios({
            method: 'put',
            url: backendSettings.TE_BASEPATH + '/api/v1/tiny_url',
            data: data
        }).then((response) => {
            props.showAlerts(response.data.message);
        }).catch((err) => {props.showAlerts(err.response.data);});
    }

    return (
        <>
            <div className={styles.teMarginTop20}>
                <label>TinyUrl: </label>
            </div>
            <div
                className={styles.teAccordian + ' accordion md-accordion'}
                id="accordionEx2"
                role="tablist"
                aria-multiselectable="true"
            >
                <div className={styles.teScreenTable}>
                    {<div className={styles.teCard + ' card'}>
                        <div
                            className="card-header"
                            role="tab"
                            id="headingTwo22"
                        >
                            <a
                                data-toggle="collapse"
                                data-parent="#accordionEx2"
                                href="#collapseTwo22"
                                aria-expanded="true"
                                aria-controls="collapseTwo22"
                            >
                                <h5 className="mb-0">
                                    URLs{' '}
                                    <i className="fas fa-angle-down rotate-icon" />
                                </h5>
                            </a>
                        </div>
                        <div
                            id="collapseTwo22"
                            className="collapse"
                            role="tabpanel"
                            aria-labelledby="headingTwo22"
                            data-parent="#accordionEx2"
                        >
                            <div className="card-body">
                                <div className={styles.teAttributesWrapper}>
                                    {props.items.map((item, index) => (
                                        <TinyUrlDropdownComponent id={item.urlKey} key={item.urlKey} urlKey={item.urlKey} expiry={item.expiry} handleChange={handleChange} removeDropdown={removeDropdown} urlKeyList={props.urlKeyList} visited={props.visited}/>
                                    ))}
                                    {props.items.length < props.urlKeyList.length ?
                                        <button
                                            className={styles.teAddNewAttributeButton}
                                            onClick={addNewDropdown}
                                        >
                                            +
                                        </button> :
                                        ""
                                    }
                                    <button
                                        className={styles.teUpdateButton}
                                        onClick={valueSelected}
                                    >
                                        Update
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>}
                </div>
            </div>
        </>

    );
}
