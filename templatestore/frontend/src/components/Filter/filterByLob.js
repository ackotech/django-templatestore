import React, { Component } from "react";
import styles from './filter.less';
import { backendSettings } from "../../utils";

class Lob extends Component {
    constructor(props) {
        super(props);
        this.state = {
            selectValue: ""
        };

        this.handleDropdownChange = this.handleDropdownChange.bind(this);
    }

    handleDropdownChange(e) {
        this.props.onChange(e.target.value);
        this.setState({ selectValue: e.target.value });
    }

    getAttributeOptions() {
        let attribute = { };
        attribute = {
            ...backendSettings.TE_TEMPLATE_ATTRIBUTES
        };
        let allowedValues = attribute["lob"]["allowed_values"];
        var options = [];
        options.push(
            allowedValues.map(t => {
                return (<option value={t}>{t}</option>);
            })
        );
        return options;
    }

    render() {
        return (
            <div>
                <div>
                    <select id="dropdown" className={styles.filter} onChange={this.handleDropdownChange}>
                        <option value="">Choose Lob</option>
                        {
                            this.getAttributeOptions()
                        }

                    </select>
                </div>

                {/* <div>Selected value is : {this.state.selectValue}</div> */}
            </div>
        );
    }
}
export default Lob;
