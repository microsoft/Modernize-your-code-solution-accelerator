import { List,ListItem, tokens,Text } from "@fluentui/react-components";
import { DismissCircle24Regular, Warning24Regular, InfoRegular } from "@fluentui/react-icons";
import React from "react";
import "./errorComponent.scss";

const ErrorComponent = (props) => {
    const {file} = props;
    return (
      <>
        {file?.file_logs?.length > 0 ? (
          <List className="pl_16">
            {file.file_logs?.map((log, logIdx) => (
              <ListItem key={logIdx} className="ml_8">
                <Text className="infoText">
                  <span className="iconContainer">
                    {log.logType === "error" ? (
                      <DismissCircle24Regular className="errorIcon" />
                    ) : log.logType === "warning" ? (
                        <Warning24Regular className="warningIcon" />
                    ) : (
                          <InfoRegular className="infoIcon"/>
                        )}
                  </span>
                  <span>{log.agentType}: {log.description}</span>
                </Text>
              </ListItem>
            ))}
          </List>
        ) : (
          <p className="pl_24">No detailed logs available.</p>
        )}
      </>
    );
  };

  export default ErrorComponent;