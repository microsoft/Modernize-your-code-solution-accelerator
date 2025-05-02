import React from "react";
import { Toolbar } from "@fluentui/react-components";
import "./Header.scss"


interface HeaderToolsProps {
    children?: React.ReactNode;
}

const HeaderTools: React.FC<HeaderToolsProps> = ({ children }) => {


    return (
        <Toolbar
            className="toolbar"
        >
            {children}
        </Toolbar>
    );
};

export default HeaderTools;
