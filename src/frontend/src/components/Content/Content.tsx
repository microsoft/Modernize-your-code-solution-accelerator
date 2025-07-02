import React, { ReactNode, ReactElement } from "react";
import PanelToolbar from "../Panels/PanelLeftToolbar.js"; // Import to identify toolbar
import "./content.scss"; // Import for styling

interface ContentProps {
    children?: ReactNode;
}

const Content: React.FC<ContentProps> = ({ children }) => {
    const childrenArray = React.Children.toArray(children) as ReactElement[];
    const toolbar = childrenArray.find(
        (child) => React.isValidElement(child) && child.type === PanelToolbar
    );
    const content = childrenArray.filter(
        (child) => !(React.isValidElement(child) && child.type === PanelToolbar)
    );

    return (
        <div
            className="content"
        >
            {toolbar && <div className="fs_0">{toolbar}</div>}

            <div
                className="panelContent"
            >
                {content}
            </div>
        </div>
    );
};

export default Content;
